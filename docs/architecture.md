# Architecture

## Overview

`novel-agent` starts as a Python CLI. A novel project is a directory of Markdown and YAML files. The CLI loads the project bible and outline, renders a prompt template, calls an OpenAI-compatible model, then writes the result back to the project directory.

## Components

- `novel_agent.cli`: Typer command line interface.
- `novel_agent.project`: project scaffold, loading, paths, and context assembly.
- `novel_agent.models`: Pydantic models for config, characters, chapters, and state.
- `novel_agent.config`: environment-based runtime settings.
- `novel_agent.llm`: OpenAI-compatible model wrapper.
- `novel_agent.prompting`: packaged Jinja2 prompt rendering.
- `novel_agent.prompts`: editable prompt templates.

## Data Flow

```text
novel project files -> context builder -> prompt template -> LLM -> markdown output
```

## Extension Points

- Add more LLM providers behind `LLMClient`.
- Add retrieval over bible and previous chapters.
- Split workflows into planner/writer/editor/continuity agents.
- Add a Web UI after the CLI workflow is stable.
