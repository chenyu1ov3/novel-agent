# novel-agent Web UI

[中文](#中文) | [English](#english)

---

## 中文

`web/` 是 `novel-agent` 的本地优先浏览器工作台，用来操作文件型小说项目、多 Agent 写作流程和向量记忆。

## 技术栈

- Next.js App Router + React
- shadcn/ui-style 本地组件 + Tailwind CSS
- Zustand 工作区状态
- Vercel AI SDK data-stream route，用于多 Agent 运行结果流
- 围绕现有 Python CLI / 项目文件的本地 API adapter

## 本地开发

```bash
cd web
pnpm install
pnpm dev
```

打开 http://localhost:3000，然后输入本地 novel-agent 项目路径，例如：

```text
/root/novel-agent/examples/wuxia-demo
```

也可以通过环境变量设置默认项目路径：

```bash
NOVEL_AGENT_PROJECT=/path/to/my-novel pnpm dev
```

## 当前能力

- 按路径打开已有 novel-agent 项目。
- 从 `novel.yaml` 读取项目元数据。
- 浏览 `bible/`、`outlines/`、`summaries/`、`chapters/`、`scenes/`、`memory/`、`runs/` 下的项目文件。
- 通过 API routes 读写 Markdown/YAML 项目资产。
- 用 local 或 pgvector 后端触发 `novel-agent index-memory`。
- 通过 Vercel AI SDK data-stream route 触发 `novel-agent agent-run`。

## 验证

```bash
pnpm test
pnpm typecheck
pnpm build
```

## 部署说明

当前 Web UI 面向本地优先使用：它会在服务端文件系统读写小说项目文件，并调用 `novel-agent` CLI。公开托管前，需要先设计安全的项目存储方案，并加固命令执行边界。

---

## English

`web/` is the local-first browser workspace for `novel-agent`. It operates file-based novel projects, multi-agent writing workflows, and vector memory from a UI.

## Stack

- Next.js App Router + React
- shadcn/ui-style local components + Tailwind CSS
- Zustand workspace state
- Vercel AI SDK data-stream route for multi-agent run output
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
- Trigger `novel-agent agent-run` through a Vercel AI SDK data-stream route.

## Verification

```bash
pnpm test
pnpm typecheck
pnpm build
```

## Deployment note

This initial UI is designed for local-first usage because it reads and writes novel project files on the server filesystem and shells out to `novel-agent`. Hosted deployments need a secure project storage story and a hardened command execution boundary before exposing it publicly.
