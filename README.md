# novel-agent

`novel-agent` is an AI-assisted long-form novel writing agent. It keeps a novel project as readable Markdown/YAML files, then uses prompt templates and an OpenAI-compatible LLM to brainstorm, outline, draft, and review chapters.

## Why this shape?

Long-form fiction breaks when the model forgets characters, timeline, style, or previous decisions. This project keeps those assets explicit:

- `bible/`: premise, world, characters, timeline, style guide
- `outlines/`: story arc and chapter outline
- `chapters/`: generated or manually edited chapter drafts

The human author stays in control; AI output is versionable and editable.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

## Configure

Copy `.env.example` to `.env` and fill in your API key:

```env
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=replace-me
NOVEL_AGENT_MODEL=gpt-4o-mini
```

Any OpenAI-compatible provider can be used by changing `OPENAI_BASE_URL` and `NOVEL_AGENT_MODEL`.

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
- [x] Brainstorm / outline / write / review commands
- [ ] Chapter summary memory
- [ ] Continuity checker
- [ ] Scene-level drafting
- [ ] Local model support examples
- [ ] Web UI
