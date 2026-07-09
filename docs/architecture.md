# 架构说明

## 总览

`novel-agent` 是一个文件优先的多 Agent 长篇小说写作系统。小说项目仍然是一组可读、可版本控制的 Markdown/YAML 文件；写作流程则从单次 Prompt 调用升级为带检索增强的多 Agent 管线。

```text
小说项目文件
  -> 记忆索引器（本地 JSONL 或 pgvector）
  -> 检索上下文
  -> 剧情架构师
  -> 连续性守门人
  -> 场景写手
  -> 文风润色编辑
  -> 终审批评家
  -> chapters/*.md + runs/*.md 运行轨迹
```

CLI 仍保留原有轻量命令（`brainstorm`、`outline`、`write`、`review`），作者可以按需选择简单流程或复杂多 Agent 流程。

## 组件

- `novel_agent.cli`：Typer 命令行入口。
- `novel_agent.project`：项目初始化、加载、路径管理、`memory/` 与 `runs/` 目录、上下文组装。
- `novel_agent.models`：Pydantic 项目模型，包括 `AgentConfig` 和 `MemoryConfig`。
- `novel_agent.config`：运行时配置，覆盖 LLM、embedding、本地记忆和 pgvector。
- `novel_agent.llm`：OpenAI-compatible chat completions 封装。
- `novel_agent.vector_store`：检索层，支持本地 JSONL 向量、OpenAI-compatible embeddings、pgvector SQL/schema 和安全 SQL identifier 校验。
- `novel_agent.agents`：声明式 Agent registry 与章节生成 orchestrator。
- `novel_agent.prompting`：旧版单 Agent 命令使用的 Jinja2 Prompt 渲染。
- `web/`：Next.js App Router Web UI，用于本地优先的项目浏览、编辑、记忆索引和多 Agent 运行控制。

## 多 Agent 角色

默认 `agent-run` 管线使用五个专业角色：

1. **剧情架构师**（`story_architect`）：把章节目标拆成因果清晰的写作蓝图。
2. **连续性守门人**（`continuity_guardian`）：用 bible、时间线、摘要和检索记忆检查蓝图风险。
3. **场景写手**（`scene_writer`）：写具体动作、对白、环境和情绪推进。
4. **文风润色编辑**（`style_editor`）：在不改事实的前提下统一节奏、语气和画面感。
5. **终审批评家**（`critic`）：做最终质量门禁，并给出可执行修改建议。

每次运行都会写入：

- `chapters/chNNN.md` 或 `chapters/chNNN.draft.md`
- `runs/chNNN-YYYYMMDD-HHMMSS.md` 和 `.json`，保存完整 Agent trace

## 记忆与向量检索

### 本地后端

默认本地后端将向量写入：

```text
memory/vectors.jsonl
```

它使用 `HashEmbeddingProvider`，这是一个确定性的零外部依赖 embedding provider，适合测试、演示和离线开发。它不是生产级语义 embedding 的替代品。

### OpenAI-compatible embeddings

设置 `NOVEL_AGENT_EMBEDDING_MODEL` 后，会使用兼容 OpenAI embeddings API 的服务。`NOVEL_AGENT_EMBEDDING_DIMENSIONS` 应与模型输出维度保持一致。

### pgvector 后端

`PgVectorStore` 为 Postgres + pgvector 提供 schema 创建、upsert 和 cosine search：

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS novel_memory (... embedding vector(1536) ...);
CREATE INDEX ... USING ivfflat (embedding vector_cosine_ops);
```

使用 CLI 的 pgvector 后端前，需要安装可选依赖：

```bash
pip install -e '.[pgvector]'
```

配置示例：

```env
NOVEL_AGENT_MEMORY_BACKEND=pgvector
NOVEL_AGENT_PGVECTOR_DSN=postgresql://user:replace-me@localhost:5432/novel_agent
NOVEL_AGENT_PGVECTOR_TABLE=novel_memory
NOVEL_AGENT_EMBEDDING_MODEL=text-embedding-3-small
NOVEL_AGENT_EMBEDDING_DIMENSIONS=1536
```

## CLI 数据流

### 索引记忆

```bash
novel-agent index-memory ./my-novel
# 或
novel-agent index-memory ./my-novel --backend pgvector
```

会索引 `novel.yaml`、`bible/`、`outlines/`、`summaries/`、`chapters/` 和 `scenes/`。

### 运行多 Agent 章节生成

```bash
novel-agent agent-run ./my-novel --chapter 2 --goal "主角追查铜铃线索"
```

orchestrator 会检索相关记忆，然后依次通过五个 Agent 角色生成结果。

## Web UI 架构

`web/` 是本地优先的 React/Next.js 工作台：

- **框架**：Next.js App Router。
- **UI**：Tailwind CSS + shadcn/ui-style 本地组件。
- **状态管理**：Zustand（`store/novel-workspace.ts`）。
- **AI route 边界**：Vercel AI SDK data stream route（`app/api/agent/run/route.ts`）。
- **项目 adapter**：`lib/novel-agent.ts` 负责读写 Markdown/YAML 文件，并调用 Python CLI 完成记忆索引和 Agent 运行。

Web UI 继续以 Markdown/YAML 项目文件作为 source of truth。公开托管前，需要先设计安全的项目存储方案，并加固命令执行边界。

## 扩展点

- 在 `default_agent_registry()` 中添加更多角色，或提供自定义 `AgentRegistry`。
- 将 `HashEmbeddingProvider` 替换为 `OpenAIEmbeddingProvider` 或其他实现 `EmbeddingProvider` 的 provider。
- 使用 `PgVectorStore` 承载共享/服务端长期记忆。
- 在不改变项目文件结构的前提下，继续扩展 Web/API/UI 层。
- 在 `collect_project_documents()` 中增加更丰富的 chunking 和 metadata 提取。
