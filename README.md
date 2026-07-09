# novel-agent

[中文](#中文) | [English](#english)

---

## 中文

`novel-agent` 是一个面向长篇小说创作的 AI 写作智能体。它会把一本小说维护成可读、可版本控制的 Markdown/YAML 项目，然后通过 Prompt 模板和 OpenAI-compatible 模型完成灵感发散、大纲规划、章节草稿和审稿。

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
```

只要服务商兼容 OpenAI API，就可以通过修改 `OPENAI_BASE_URL` 和 `NOVEL_AGENT_MODEL` 接入，例如 OpenAI、DeepSeek、Qwen、Moonshot、OpenRouter、本地 vLLM 等。

> 注意：不要提交真实 `.env`，仓库只提交 `.env.example`。

## 快速开始

```bash
novel-agent init ./my-novel --title "雪落长安" --genre "武侠悬疑"
novel-agent brainstorm ./my-novel --idea "一个失忆剑客发现自己曾是反派"
novel-agent outline ./my-novel
novel-agent write ./my-novel --chapter 1 --goal "主角在雪夜发现第一具尸体"
novel-agent review ./my-novel --chapter 1
```

如果 `chapters/ch001.md` 已经存在，`write` 默认不会覆盖它，而是写入 `chapters/ch001.draft.md`。如果确实要覆盖，使用 `--force`。

## 命令列表

```bash
novel-agent --help
novel-agent init PATH --title TITLE --genre GENRE
novel-agent brainstorm PATH --idea IDEA
novel-agent outline PATH
novel-agent write PATH --chapter 1 --goal GOAL
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
│   └── chapters.md
└── chapters/
    └── ch001.md
```

## 开发

```bash
pytest -q
ruff check .
mypy src/novel_agent
```

## 路线图

- [x] CLI 项目骨架
- [x] 文件型小说 bible 和大纲结构
- [x] OpenAI-compatible LLM 封装
- [x] Prompt 模板
- [x] `brainstorm` / `outline` / `write` / `review` 命令
- [ ] 章节摘要记忆
- [ ] 一致性检查器
- [ ] 场景级写作
- [ ] 本地模型使用示例
- [ ] Web UI

---

## English

`novel-agent` is an AI-assisted long-form novel writing agent. It keeps a novel project as readable, version-controllable Markdown/YAML files, then uses prompt templates and an OpenAI-compatible LLM to brainstorm, outline, draft, and review chapters.

The default focus is **Chinese long-form genre fiction / web novel assisted writing**.

## Why this shape?

Long-form fiction often breaks when the model forgets characters, timeline, style, foreshadowing, or previous decisions. `novel-agent` makes those assets explicit:

- `bible/`: premise, world, characters, timeline, style guide
- `outlines/`: story arc and chapter outline
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
```

Any OpenAI-compatible provider can be used by changing `OPENAI_BASE_URL` and `NOVEL_AGENT_MODEL`, including OpenAI, DeepSeek, Qwen, Moonshot, OpenRouter, or a local vLLM endpoint.

> Do not commit a real `.env`; only `.env.example` belongs in the repository.

## Quick start

```bash
novel-agent init ./my-novel --title "雪落长安" --genre "武侠悬疑"
novel-agent brainstorm ./my-novel --idea "一个失忆剑客发现自己曾是反派"
novel-agent outline ./my-novel
novel-agent write ./my-novel --chapter 1 --goal "主角在雪夜发现第一具尸体"
novel-agent review ./my-novel --chapter 1
```

If `chapters/ch001.md` already exists, `write` will create `chapters/ch001.draft.md` unless `--force` is used.

## Commands

```bash
novel-agent --help
novel-agent init PATH --title TITLE --genre GENRE
novel-agent brainstorm PATH --idea IDEA
novel-agent outline PATH
novel-agent write PATH --chapter 1 --goal GOAL
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
│   └── chapters.md
└── chapters/
    └── ch001.md
```

## Development

```bash
pytest -q
ruff check .
mypy src/novel_agent
```

## Roadmap

- [x] CLI project scaffold
- [x] File-based novel bible and outline structure
- [x] OpenAI-compatible LLM wrapper
- [x] Prompt templates
- [x] `brainstorm` / `outline` / `write` / `review` commands
- [ ] Chapter summary memory
- [ ] Continuity checker
- [ ] Scene-level drafting
- [ ] Local model support examples
- [ ] Web UI
