# Architecture

## Overview

`novel-agent` is now a file-first, multi-agent long-form fiction system. A novel project remains a readable Markdown/YAML directory, but the writing path is upgraded from a single prompt call into a retrieval-augmented agent pipeline.

```text
novel project files
  -> memory indexer (local JSONL or pgvector)
  -> retrieval context
  -> story architect
  -> continuity guardian
  -> scene writer
  -> style editor
  -> critic
  -> chapters/*.md + runs/*.md trace
```

The CLI still preserves the original simple commands (`brainstorm`, `outline`, `write`, `review`), so authors can use either the lightweight flow or the more complex multi-agent flow.

## Components

- `novel_agent.cli`: Typer command line interface.
- `novel_agent.project`: project scaffold, loading, paths, memory/runs directories, and context assembly.
- `novel_agent.models`: Pydantic project models, including `AgentConfig` and `MemoryConfig`.
- `novel_agent.config`: environment-based runtime settings for LLMs, embeddings, local memory, and pgvector.
- `novel_agent.llm`: OpenAI-compatible chat-completions wrapper.
- `novel_agent.vector_store`: retrieval layer with local JSONL vectors, OpenAI-compatible embeddings, pgvector SQL/schema support, and safe SQL identifier validation.
- `novel_agent.agents`: declarative agent registry and chapter-drafting orchestrator.
- `novel_agent.prompting`: packaged Jinja2 prompt rendering for legacy single-agent commands.
- `web/`: Next.js App Router Web UI for local-first project browsing, editing, memory indexing, and multi-agent run control.

## Multi-Agent Roles

The default `agent-run` pipeline uses five specialist roles:

1. **Story Architect** (`story_architect`) — turns the chapter goal into a causal writing blueprint.
2. **Continuity Guardian** (`continuity_guardian`) — checks the blueprint against bible, timeline, summaries, and retrieved memories.
3. **Scene Writer** (`scene_writer`) — drafts concrete scenes with action, dialogue, environment, and emotional movement.
4. **Style Editor** (`style_editor`) — improves rhythm and voice without changing established facts.
5. **Critic** (`critic`) — performs a final quality gate and produces an actionable review.

Every run writes both:

- `chapters/chNNN.md` or `chapters/chNNN.draft.md`
- `runs/chNNN-YYYYMMDD-HHMMSS.md` and `.json` with the full agent trace

## Memory and Vector Search

### Local backend

The default local backend stores vectors in:

```text
memory/vectors.jsonl
```

It uses `HashEmbeddingProvider`, a deterministic dependency-free embedding provider. This is good for tests, demos, and offline development. It is not intended to match production embedding quality.

### OpenAI-compatible embeddings

Set `NOVEL_AGENT_EMBEDDING_MODEL` to use the embeddings API exposed by OpenAI-compatible providers. Keep `NOVEL_AGENT_EMBEDDING_DIMENSIONS` aligned with the model output dimension.

### pgvector backend

`PgVectorStore` provides schema creation, upsert, and cosine search SQL for Postgres with pgvector:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS novel_memory (... embedding vector(1536) ...);
CREATE INDEX ... USING ivfflat (embedding vector_cosine_ops);
```

Install the optional dependency before using it from the CLI:

```bash
pip install -e '.[pgvector]'
```

Then configure:

```env
NOVEL_AGENT_MEMORY_BACKEND=pgvector
NOVEL_AGENT_PGVECTOR_DSN=postgresql://user:password@localhost:5432/novel_agent
NOVEL_AGENT_PGVECTOR_TABLE=novel_memory
NOVEL_AGENT_EMBEDDING_MODEL=text-embedding-3-small
NOVEL_AGENT_EMBEDDING_DIMENSIONS=1536
```

## CLI Data Flow

### Index memory

```bash
novel-agent index-memory ./my-novel
# or
novel-agent index-memory ./my-novel --backend pgvector
```

Indexed files include `novel.yaml`, `bible/`, `outlines/`, `summaries/`, `chapters/`, and `scenes/`.

### Run the multi-agent drafter

```bash
novel-agent agent-run ./my-novel --chapter 2 --goal "主角追查铜铃线索"
```

The orchestrator retrieves relevant memory, then passes the result through the five-agent pipeline.

## Web UI Architecture

The `web/` app is a local-first React/Next.js workspace:

- **Framework:** Next.js App Router.
- **UI:** Tailwind CSS with shadcn/ui-style local primitives.
- **State:** Zustand (`store/novel-workspace.ts`).
- **AI route boundary:** Vercel AI SDK data stream route at `app/api/agent/run/route.ts`.
- **Project adapter:** `lib/novel-agent.ts` reads/writes Markdown/YAML files and invokes the Python CLI for memory indexing and agent runs.

The Web UI deliberately keeps Markdown/YAML project files as the source of truth. Hosted deployments need a hardened storage and command-execution boundary before public exposure.

## Extension Points

- Add more roles to `default_agent_registry()` or provide a custom `AgentRegistry`.
- Swap `HashEmbeddingProvider` for `OpenAIEmbeddingProvider` or another provider implementing `EmbeddingProvider`.
- Use `PgVectorStore` for shared/server-side memory.
- Add web/API/UI layers on top of `MultiAgentOrchestrator` without changing project files.
- Add richer chunking and metadata extraction in `collect_project_documents()`.
