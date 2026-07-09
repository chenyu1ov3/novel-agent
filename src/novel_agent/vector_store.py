from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Protocol

from openai import OpenAI

from novel_agent.project import NovelProject

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class VectorDocument:
    """A chunk of novel-project memory that can be embedded and retrieved."""

    document_id: str
    source_path: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VectorSearchResult:
    """A retrieved memory chunk plus a normalized similarity score."""

    document: VectorDocument
    score: float


class EmbeddingProvider(Protocol):
    """Minimal embedding interface used by vector stores."""

    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple texts into fixed-size vectors."""


class HashEmbeddingProvider:
    """Dependency-free deterministic embeddings for local development and tests.

    Production deployments should use an embedding model and store those vectors in
    pgvector. This provider intentionally keeps the CLI usable before credentials
    are configured: it hashes character n-grams into a normalized dense vector.
    """

    def __init__(self, *, dimensions: int = 256) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _features(text):
            digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
            index = int.from_bytes(digest, "big") % self.dimensions
            vector[index] += 1.0
        return _normalize(vector)


class OpenAIEmbeddingProvider:
    """OpenAI-compatible embedding provider for production retrieval.

    Many providers expose the OpenAI embeddings API. Keep this class small and
    injectable so tests can pass a fake client and deployments can point
    OPENAI_BASE_URL at OpenAI, Qwen, local vLLM-compatible services, etc.
    """

    def __init__(
        self,
        *,
        model: str,
        dimensions: int,
        api_key: str | None = None,
        base_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self.model = model
        self.dimensions = dimensions
        self._client: Any = client or OpenAI(api_key=api_key, base_url=base_url)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        kwargs: dict[str, Any] = {"model": self.model, "input": texts}
        # text-embedding-3* supports custom dimensions. Providers that reject
        # the parameter can set NOVEL_AGENT_EMBEDDING_DIMENSIONS to the model's
        # native size and use an OpenAI-compatible endpoint that accepts it.
        kwargs["dimensions"] = self.dimensions
        # Some OpenAI-compatible providers do not support the dimensions
        # parameter. Retry without it while preserving the configured dimension
        # validation below, so a mismatch is still caught loudly.
        try:
            response = self._client.embeddings.create(**kwargs)
        except TypeError:
            kwargs.pop("dimensions", None)
            response = self._client.embeddings.create(**kwargs)
        vectors = [list(item.embedding) for item in response.data]
        for vector in vectors:
            if len(vector) != self.dimensions:
                raise ValueError(
                    f"embedding model returned {len(vector)} dimensions; expected {self.dimensions}"
                )
        return vectors


class VectorStore(Protocol):
    """Minimal vector store contract used by the retrieval engine."""

    dimensions: int

    def upsert(self, documents: list[VectorDocument], embeddings: list[list[float]]) -> None:
        """Insert or replace documents with precomputed embeddings."""

    def search(self, query_embedding: list[float], *, limit: int = 8) -> list[VectorSearchResult]:
        """Return nearest documents for a query embedding."""


class LocalVectorStore:
    """Small JSONL-backed vector store for offline use and tests.

    It mirrors the vector-store API used by pgvector without requiring Postgres.
    The persisted file is intentionally transparent so authors can inspect and
    delete local memory during experimentation.
    """

    def __init__(self, *, dimensions: int = 256, persist_path: Path | None = None) -> None:
        self.dimensions = dimensions
        self.persist_path = persist_path
        self._rows: dict[str, tuple[VectorDocument, list[float]]] = {}
        if persist_path is not None and persist_path.exists():
            self._load()

    def upsert(self, documents: list[VectorDocument], embeddings: list[list[float]]) -> None:
        if len(documents) != len(embeddings):
            raise ValueError("documents and embeddings must have the same length")
        for document, embedding in zip(documents, embeddings, strict=True):
            self._validate_embedding(embedding)
            self._rows[document.document_id] = (document, _normalize(embedding))
        self._persist()

    def index_project(self, project: NovelProject, embeddings: EmbeddingProvider) -> int:
        documents = collect_project_documents(project)
        vectors = embeddings.embed_documents([document.content for document in documents])
        self.upsert(documents, vectors)
        return len(documents)

    def search(self, query_embedding: list[float], *, limit: int = 8) -> list[VectorSearchResult]:
        self._validate_embedding(query_embedding)
        normalized_query = _normalize(query_embedding)
        results = [
            VectorSearchResult(document=document, score=_cosine(normalized_query, embedding))
            for document, embedding in self._rows.values()
        ]
        results.sort(key=lambda result: result.score, reverse=True)
        return results[:limit]

    def _validate_embedding(self, embedding: list[float]) -> None:
        if len(embedding) != self.dimensions:
            raise ValueError(f"expected embedding with {self.dimensions} dimensions")

    def _load(self) -> None:
        assert self.persist_path is not None
        for line in self.persist_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            document = VectorDocument(
                document_id=row["document_id"],
                source_path=row["source_path"],
                content=row["content"],
                metadata=row.get("metadata", {}),
            )
            self._rows[document.document_id] = (document, row["embedding"])

    def _persist(self) -> None:
        if self.persist_path is None:
            return
        self.persist_path.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for document, embedding in self._rows.values():
            lines.append(
                json.dumps(
                    {
                        "document_id": document.document_id,
                        "source_path": document.source_path,
                        "content": document.content,
                        "metadata": document.metadata,
                        "embedding": embedding,
                    },
                    ensure_ascii=False,
                )
            )
        self.persist_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


class PgVectorStore:
    """pgvector-backed store for production-scale project memory.

    The class uses a DB-API/psycopg style connection object. Passing a connection
    keeps tests and applications flexible while still documenting the SQL needed
    for managed Postgres providers that support pgvector.
    """

    def __init__(self, *, connection: Any, table_name: str = "novel_memory", dimensions: int = 1536) -> None:
        self.connection = connection
        self.table_name = validate_pgvector_identifier(table_name)
        self.dimensions = dimensions

    @staticmethod
    def schema_sql(*, table_name: str = "novel_memory", dimensions: int = 1536) -> str:
        table = validate_pgvector_identifier(table_name)
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        return f"""CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS {table} (
    document_id text PRIMARY KEY,
    source_path text NOT NULL,
    content text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{{}}'::jsonb,
    embedding vector({dimensions}) NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS {table}_embedding_idx
    ON {table} USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
"""

    def ensure_schema(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(self.schema_sql(table_name=self.table_name, dimensions=self.dimensions))
        self.connection.commit()

    def index_project(self, project: NovelProject, embeddings: EmbeddingProvider) -> int:
        documents = collect_project_documents(project)
        vectors = embeddings.embed_documents([document.content for document in documents])
        self.upsert(documents, vectors)
        return len(documents)

    def upsert(self, documents: list[VectorDocument], embeddings: list[list[float]]) -> None:
        if len(documents) != len(embeddings):
            raise ValueError("documents and embeddings must have the same length")
        sql = f"""
INSERT INTO {self.table_name} (document_id, source_path, content, metadata, embedding, updated_at)
VALUES (%s, %s, %s, %s, %s, now())
ON CONFLICT (document_id) DO UPDATE SET
    source_path = EXCLUDED.source_path,
    content = EXCLUDED.content,
    metadata = EXCLUDED.metadata,
    embedding = EXCLUDED.embedding,
    updated_at = now()
"""
        with self.connection.cursor() as cursor:
            for document, embedding in zip(documents, embeddings, strict=True):
                if len(embedding) != self.dimensions:
                    raise ValueError(f"expected embedding with {self.dimensions} dimensions")
                cursor.execute(
                    sql,
                    (
                        document.document_id,
                        document.source_path,
                        document.content,
                        json.dumps(document.metadata, ensure_ascii=False),
                        _pgvector_literal(_normalize(embedding)),
                    ),
                )
        self.connection.commit()

    def search(self, query_embedding: list[float], *, limit: int = 8) -> list[VectorSearchResult]:
        if len(query_embedding) != self.dimensions:
            raise ValueError(f"expected embedding with {self.dimensions} dimensions")
        sql = f"""
SELECT document_id, source_path, content, metadata, 1 - (embedding <=> %s::vector) AS score
FROM {self.table_name}
ORDER BY embedding <=> %s::vector
LIMIT %s
"""
        query = _pgvector_literal(_normalize(query_embedding))
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (query, query, limit))
            rows = cursor.fetchall()
        return [
            VectorSearchResult(
                document=VectorDocument(
                    document_id=row[0],
                    source_path=row[1],
                    content=row[2],
                    metadata=row[3] or {},
                ),
                score=float(row[4]),
            )
            for row in rows
        ]


@dataclass(frozen=True)
class RetrievalEngine:
    """Query helper that embeds search text and formats memory for prompts."""

    store: VectorStore
    embeddings: EmbeddingProvider

    def search(self, query: str, *, limit: int = 8) -> list[VectorSearchResult]:
        query_embedding = self.embeddings.embed_documents([query])[0]
        return self.store.search(query_embedding, limit=limit)

    def context_block(self, query: str, *, limit: int = 8) -> str:
        results = self.search(query, limit=limit)
        if not results:
            return ""
        blocks = []
        for result in results:
            blocks.append(
                f"## {result.document.source_path} (score={result.score:.3f})\n\n{result.document.content}"
            )
        return "\n\n".join(blocks)


def collect_project_documents(project: NovelProject) -> list[VectorDocument]:
    """Collect Markdown/YAML project assets into retrievable memory chunks."""

    include_dirs = ["bible", "outlines", "summaries", "chapters", "scenes"]
    documents: list[VectorDocument] = []
    for relative in ["novel.yaml"]:
        path = project.root / relative
        if path.exists():
            documents.extend(_documents_from_path(project.root, path, kind="config"))
    for directory in include_dirs:
        root = project.root / directory
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix.lower() not in {".md", ".yaml", ".yml"} or not path.is_file():
                continue
            documents.extend(_documents_from_path(project.root, path, kind=directory))
    return documents


def validate_pgvector_identifier(identifier: str) -> str:
    if not _IDENTIFIER_RE.match(identifier):
        raise ValueError(f"Unsafe SQL identifier: {identifier!r}")
    return identifier


def _documents_from_path(project_root: Path, path: Path, *, kind: str) -> list[VectorDocument]:
    relative = path.relative_to(project_root).as_posix()
    text = path.read_text(encoding="utf-8")
    chunks = list(_chunk_text(text))
    documents = []
    for index, chunk in enumerate(chunks, start=1):
        document_id = hashlib.sha1(f"{relative}:{index}:{chunk}".encode("utf-8")).hexdigest()
        documents.append(
            VectorDocument(
                document_id=document_id,
                source_path=relative if len(chunks) == 1 else f"{relative}#chunk-{index}",
                content=chunk,
                metadata={"kind": kind, "chunk": index},
            )
        )
    return documents


def _chunk_text(text: str, *, max_chars: int = 1800) -> Iterable[str]:
    stripped = text.strip()
    if not stripped:
        return []
    if len(stripped) <= max_chars:
        return [stripped]
    paragraphs = [paragraph.strip() for paragraph in stripped.split("\n\n") if paragraph.strip()]
    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = paragraph
    if current:
        chunks.append(current)
    return chunks


def _features(text: str) -> list[str]:
    normalized = re.sub(r"\s+", "", text.lower())
    words = re.findall(r"[a-z0-9_]+", text.lower())
    features = words[:]
    for width in (1, 2, 3):
        features.extend(normalized[index : index + width] for index in range(max(0, len(normalized) - width + 1)))
    return [feature for feature in features if feature]


def _normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _pgvector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in vector) + "]"
