# novel-agent

[中文](#中文) | [English](#english)

---

## 中文

`novel-agent` 是一个面向长篇小说创作的 AI 写作智能体。它会把一本小说维护成可读、可版本控制的 Markdown/YAML 项目，然后通过 Prompt 模板、向量记忆和多 Agent 编排完成灵感发散、大纲规划、章节草稿、连续性检查和审稿。

默认目标是：**中文长篇类型小说 / 网文辅助创作**。

## 为什么这样设计？

长篇小说最容易崩在这些地方：

- 人物动机前后不一致
- 世界观和时间线冲突
- 写着写着忘记伏笔
- 模型自由发挥导致剧情跑偏
- AI 腔严重，缺少具体动作、场景和对白

所以 `novel-agent` 不把 AI 当成一次性“自动写完整本书”的黑盒，而是把创作资产显式保存下来：

- `bible/`：梗概、世界观、角色卡、时间线、文风指南
- `outlines/`：主线大纲、章节大纲
- `summaries/`：章节摘要和长期剧情记忆
- `memory/`：本地向量索引（可替换为 pgvector）
- `runs/`：多 Agent 运行轨迹，便于复盘每一步决策
- `chapters/`：生成或人工修改后的章节草稿

人类作者保留最终控制权，AI 输出可以编辑、diff、回滚和持续迭代。

## 安装

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## 配置模型

复制 `.env.example` 为 `.env`，然后填入你的 API Key：

```bash
cp .env.example .env
```

`.env` 示例：

```env
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=replace-me
NOVEL_AGENT_MODEL=gpt-4o-mini

# 默认本地向量记忆：无需额外服务
NOVEL_AGENT_MEMORY_BACKEND=local
NOVEL_AGENT_EMBEDDING_MODEL=
NOVEL_AGENT_EMBEDDING_DIMENSIONS=256
```

只要服务商兼容 OpenAI API，就可以通过修改 `OPENAI_BASE_URL` 和 `NOVEL_AGENT_MODEL` 接入，例如 OpenAI、DeepSeek、Qwen、Moonshot、OpenRouter、本地 vLLM 等。

如果要启用生产级 embedding + pgvector：

```bash
pip install -e '.[pgvector]'
```

```env
NOVEL_AGENT_MEMORY_BACKEND=pgvector
NOVEL_AGENT_EMBEDDING_MODEL=text-embedding-3-small
NOVEL_AGENT_EMBEDDING_DIMENSIONS=1536
NOVEL_AGENT_PGVECTOR_DSN=postgresql://user:replace-me@localhost:5432/novel_agent
NOVEL_AGENT_PGVECTOR_TABLE=novel_memory
```

> 注意：不要提交真实 `.env`，仓库只提交 `.env.example`。

## 快速开始

```bash
novel-agent init ./my-novel --title "雪落长安" --genre "武侠悬疑"
novel-agent brainstorm ./my-novel --idea "一个失忆剑客发现自己曾是反派"
novel-agent outline ./my-novel
novel-agent index-memory ./my-novel
novel-agent agent-run ./my-novel --chapter 1 --goal "失忆剑客在雪夜发现第一条旧案线索"
novel-agent plan-scenes ./my-novel --chapter 1
novel-agent write-scene ./my-novel --chapter 1 --scene 1
novel-agent compose-chapter ./my-novel --chapter 1
novel-agent summarize ./my-novel --chapter 1
novel-agent continuity ./my-novel --chapter 1
novel-agent review ./my-novel --chapter 1
```

如果 `chapters/ch001.md` 已经存在，`write` 默认不会覆盖它，而是写入 `chapters/ch001.draft.md`。如果确实要覆盖，使用 `--force`。

`summarize` 会把章节正文压缩成可复用的长篇记忆，写入 `summaries/ch001.md`。后续写第 N 章时，`write` 会自动读取前面章节的摘要，帮助模型保持剧情、人物和伏笔连续。

`continuity` 会把章节正文与项目设定、角色卡、时间线、大纲和前文摘要进行对照，输出 `chapters/ch001.continuity.md`，用于发现人物动机、时间线、世界观、伏笔和文风方面的连续性问题。

如果想更稳定地写长章节，可以使用场景级流程：`plan-scenes` 先规划一章的多个场景，`write-scene` 单独写某个场景，`compose-chapter` 再按顺序合并成章节正文。

## 命令列表

```bash
novel-agent --help
novel-agent init PATH --title TITLE --genre GENRE
novel-agent brainstorm PATH --idea IDEA
novel-agent outline PATH
novel-agent write PATH --chapter 1 --goal GOAL
novel-agent index-memory PATH [--backend local|pgvector]
novel-agent agent-run PATH --chapter 1 --goal GOAL
novel-agent plan-scenes PATH --chapter 1
novel-agent write-scene PATH --chapter 1 --scene 1
novel-agent compose-chapter PATH --chapter 1
novel-agent summarize PATH --chapter 1
novel-agent continuity PATH --chapter 1
novel-agent review PATH --chapter 1
```

## 小说项目结构

初始化后的小说项目大致如下：

```text
my-novel/
├── novel.yaml
├── bible/
│   ├── premise.md
│   ├── world.md
│   ├── characters.md
│   ├── timeline.md
│   └── style.md
├── outlines/
│   ├── arc.md
│   ├── chapters.md
│   └── scenes/
│       └── ch001.md
├── scenes/
│   └── ch001/
│       ├── s001.md
│       └── s002.md
├── memory/
│   └── vectors.jsonl
├── runs/
│   └── ch001-YYYYMMDD-HHMMSS.md
├── chapters/
│   ├── ch001.md
│   └── ch001.continuity.md
└── summaries/
    └── ch001.md
```

## 开发

Python CLI：

```bash
pytest -q
ruff check .
mypy src/novel_agent
```

Web UI：

```bash
cd web
pnpm install
pnpm dev
```

See `web/README.md` for the React/Next.js Web UI. It provides a local-first browser workspace built with shadcn/ui-style components, Tailwind CSS, Vercel AI SDK routes, and Zustand state.

## 路线图

- [x] CLI 项目骨架
- [x] 文件型小说 bible 和大纲结构
- [x] OpenAI-compatible LLM 封装
- [x] Prompt 模板
- [x] `brainstorm` / `outline` / `write` / `review` 命令
- [x] 章节摘要记忆
- [x] 一致性检查器
- [x] 场景级写作
- [x] 多 Agent 章节生成管线
- [x] 本地向量记忆与 pgvector 架构支持
- [x] Web UI（React / Next.js / shadcn/ui-style / Vercel AI SDK / Zustand）

---

## English

`novel-agent` is an AI-assisted long-form novel writing agent. It keeps a novel project as readable, version-controllable Markdown/YAML files, then uses prompt templates, vector memory, and multi-agent orchestration to brainstorm, outline, draft, check continuity, and review chapters.

The default focus is **Chinese long-form genre fiction / web novel assisted writing**.

## Why this shape?

Long-form fiction often breaks when the model forgets characters, timeline, style, foreshadowing, or previous decisions. `novel-agent` makes those assets explicit:

- `bible/`: premise, world, characters, timeline, style guide
- `outlines/`: story arc and chapter outline
- `summaries/`: reusable chapter summaries and long-form memory
- `memory/`: local vector index, replaceable with pgvector
- `runs/`: multi-agent traces for every orchestrated chapter run
- `chapters/`: generated or manually edited chapter drafts

The human author stays in control; AI output is editable, diffable, reversible, and iterative.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Configure

Copy `.env.example` to `.env` and fill in your API key:

```bash
cp .env.example .env
```

Example `.env`:

```env
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=replace-me
NOVEL_AGENT_MODEL=gpt-4o-mini

# Default local vector memory: no extra service required
NOVEL_AGENT_MEMORY_BACKEND=local
NOVEL_AGENT_EMBEDDING_MODEL=
NOVEL_AGENT_EMBEDDING_DIMENSIONS=256
```

Any OpenAI-compatible provider can be used by changing `OPENAI_BASE_URL` and `NOVEL_AGENT_MODEL`, including OpenAI, DeepSeek, Qwen, Moonshot, OpenRouter, or a local vLLM endpoint.

For production embeddings + pgvector:

```bash
pip install -e '.[pgvector]'
```

```env
NOVEL_AGENT_MEMORY_BACKEND=pgvector
NOVEL_AGENT_EMBEDDING_MODEL=text-embedding-3-small
NOVEL_AGENT_EMBEDDING_DIMENSIONS=1536
NOVEL_AGENT_PGVECTOR_DSN=postgresql://user:replace-me@localhost:5432/novel_agent
NOVEL_AGENT_PGVECTOR_TABLE=novel_memory
```

> Do not commit a real `.env`; only `.env.example` belongs in the repository.

## Quick start

```bash
novel-agent init ./my-novel --title "雪落长安" --genre "武侠悬疑"
novel-agent brainstorm ./my-novel --idea "一个失忆剑客发现自己曾是反派"
novel-agent outline ./my-novel
novel-agent index-memory ./my-novel
novel-agent agent-run ./my-novel --chapter 1 --goal "失忆剑客在雪夜发现第一条旧案线索"
novel-agent plan-scenes ./my-novel --chapter 1
novel-agent write-scene ./my-novel --chapter 1 --scene 1
novel-agent compose-chapter ./my-novel --chapter 1
novel-agent summarize ./my-novel --chapter 1
novel-agent continuity ./my-novel --chapter 1
novel-agent review ./my-novel --chapter 1
```

If `chapters/ch001.md` already exists, `write` will create `chapters/ch001.draft.md` unless `--force` is used.

`summarize` compresses a chapter into reusable long-form memory under `summaries/ch001.md`. When drafting chapter N, `write` can include previous chapter summaries so the model keeps plot, character, and foreshadowing continuity.

`continuity` checks a chapter against the project bible, character cards, timeline, outline, and previous summaries, then writes `chapters/ch001.continuity.md` with concrete continuity issues and revision suggestions.

For more stable long chapters, use the scene-level flow: `plan-scenes` plans scenes for a chapter, `write-scene` drafts one scene, and `compose-chapter` combines scene drafts in order.

## Commands

```bash
novel-agent --help
novel-agent init PATH --title TITLE --genre GENRE
novel-agent brainstorm PATH --idea IDEA
novel-agent outline PATH
novel-agent write PATH --chapter 1 --goal GOAL
novel-agent index-memory PATH [--backend local|pgvector]
novel-agent agent-run PATH --chapter 1 --goal GOAL
novel-agent plan-scenes PATH --chapter 1
novel-agent write-scene PATH --chapter 1 --scene 1
novel-agent compose-chapter PATH --chapter 1
novel-agent summarize PATH --chapter 1
novel-agent continuity PATH --chapter 1
novel-agent review PATH --chapter 1
```

## Novel project structure

```text
my-novel/
├── novel.yaml
├── bible/
│   ├── premise.md
│   ├── world.md
│   ├── characters.md
│   ├── timeline.md
│   └── style.md
├── outlines/
│   ├── arc.md
│   ├── chapters.md
│   └── scenes/
│       └── ch001.md
├── scenes/
│   └── ch001/
│       ├── s001.md
│       └── s002.md
├── memory/
│   └── vectors.jsonl
├── runs/
│   └── ch001-YYYYMMDD-HHMMSS.md
├── chapters/
│   ├── ch001.md
│   └── ch001.continuity.md
└── summaries/
    └── ch001.md
```

## Development

Python CLI:

```bash
pytest -q
ruff check .
mypy src/novel_agent
```

Web UI:

```bash
cd web
pnpm install
pnpm dev
```

See `web/README.md` for the React/Next.js Web UI. It provides a local-first browser workspace built with shadcn/ui-style components, Tailwind CSS, Vercel AI SDK routes, and Zustand state.

## Roadmap

- [x] CLI project scaffold
- [x] File-based novel bible and outline structure
- [x] OpenAI-compatible LLM wrapper
- [x] Prompt templates
- [x] `brainstorm` / `outline` / `write` / `review` commands
- [x] Chapter summary memory
- [x] Continuity checker
- [x] Scene-level drafting
- [x] Multi-agent chapter drafting pipeline
- [x] Local vector memory and pgvector architecture support
- [x] Web UI (React / Next.js / shadcn/ui-style / Vercel AI SDK / Zustand)
