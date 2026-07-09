# novel-agent Web UI

Modern browser workspace for the file-first `novel-agent` workflow.

## Stack

- Next.js App Router + React
- shadcn/ui-style local components + Tailwind CSS
- Zustand workspace state
- Vercel AI SDK data-stream route for multi-agent runs
- Local API adapter around the existing Python CLI / project files

## Local development

```bash
cd web
pnpm install
pnpm dev
```

Open http://localhost:3000 and enter a local novel-agent project path, for example:

```text
/root/novel-agent/examples/wuxia-demo
```

You can also set a default project path:

```bash
NOVEL_AGENT_PROJECT=/path/to/my-novel pnpm dev
```

## Current capabilities

- Open an existing novel-agent project by path.
- Read metadata from `novel.yaml`.
- Browse project files under `bible/`, `outlines/`, `summaries/`, `chapters/`, `scenes/`, `memory/`, and `runs/`.
- Read/write Markdown/YAML project assets through API routes.
- Trigger `novel-agent index-memory` with local or pgvector backend.
- Trigger `novel-agent agent-run` through a Vercel AI SDK data stream route.

## Verification

```bash
pnpm test
pnpm typecheck
pnpm build
```

## Deployment note

This initial UI is designed for local-first usage because it reads and writes novel project files on the server filesystem and shells out to `novel-agent`. Hosted deployments need a secure project storage story and a hardened command execution boundary before exposing it publicly.
