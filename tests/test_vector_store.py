import pytest

from novel_agent.project import NovelProject
from novel_agent.vector_store import (
    HashEmbeddingProvider,
    LocalVectorStore,
    OpenAIEmbeddingProvider,
    PgVectorStore,
    RetrievalEngine,
    VectorDocument,
    validate_pgvector_identifier,
)


def test_local_vector_store_returns_relevant_project_memory(tmp_path):
    project = NovelProject.init(tmp_path / "demo", title="雪落长安", genre="武侠")
    (project.root / "bible" / "characters.md").write_text(
        "# Characters\n\n沈青随身带着一枚铜铃，这是玄灯旧案的关键线索。",
        encoding="utf-8",
    )

    embeddings = HashEmbeddingProvider(dimensions=32)
    store = LocalVectorStore(dimensions=32)
    count = store.index_project(project, embeddings)

    assert count > 0
    results = RetrievalEngine(store=store, embeddings=embeddings).search("铜铃", limit=3)
    assert results
    assert any("铜铃" in result.document.content for result in results)


def test_local_vector_store_can_persist_and_reload(tmp_path):
    path = tmp_path / "memory" / "vectors.jsonl"
    store = LocalVectorStore(dimensions=8, persist_path=path)
    embeddings = HashEmbeddingProvider(dimensions=8)
    document = VectorDocument(
        document_id="doc-1",
        source_path="bible/world.md",
        content="长安城地下有旧阵。",
        metadata={"kind": "bible"},
    )

    store.upsert([document], embeddings.embed_documents([document.content]))
    reloaded = LocalVectorStore(dimensions=8, persist_path=path)

    results = RetrievalEngine(store=reloaded, embeddings=embeddings).search("旧阵", limit=1)
    assert results[0].document.document_id == "doc-1"


def test_openai_embedding_provider_uses_configured_model_and_dimensions():
    class FakeEmbeddings:
        def create(self, **kwargs):
            self.last_kwargs = kwargs
            item = type("Embedding", (), {"embedding": [0.1, 0.2, 0.3]})()
            return type("EmbeddingResponse", (), {"data": [item]})()

    class FakeOpenAIClient:
        def __init__(self):
            self.embeddings = FakeEmbeddings()

    fake_client = FakeOpenAIClient()
    provider = OpenAIEmbeddingProvider(model="text-embedding-3-small", dimensions=3, client=fake_client)

    vectors = provider.embed_documents(["铜铃线索"])

    assert vectors == [[0.1, 0.2, 0.3]]
    assert fake_client.embeddings.last_kwargs == {
        "model": "text-embedding-3-small",
        "input": ["铜铃线索"],
        "dimensions": 3,
    }


def test_pgvector_schema_sql_contains_extension_table_and_index():
    sql = PgVectorStore.schema_sql(table_name="novel_memory", dimensions=1536)

    assert "CREATE EXTENSION IF NOT EXISTS vector" in sql
    assert "embedding vector(1536)" in sql
    assert "novel_memory_embedding_idx" in sql
    assert "ivfflat" in sql


@pytest.mark.parametrize("unsafe", ["novel-memory", "novel_memory;drop", "123bad", "with space"])
def test_pgvector_identifier_validation_rejects_unsafe_names(unsafe):
    with pytest.raises(ValueError):
        validate_pgvector_identifier(unsafe)
