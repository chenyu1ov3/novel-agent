# Novel Agent 产品简报

## 定位

`novel-agent` 是一个面向中文长篇类型小说创作者的 AI 写作系统。它不是一次性“帮我写一本书”的黑盒，而是一个能维护小说项目状态、检索长期记忆、协调多个专业 Agent、持续生成章节、审稿并支持人工迭代的写作管线。

## 目标用户

- 独立作者
- 网文作者
- 想用 AI 辅助搭建世界观、大纲和章节草稿的人
- 想把设定、伏笔、摘要和草稿沉淀成可检索长期记忆的创作者

## 核心场景

1. 输入一个灵感。
2. 生成 premise、世界观、角色卡和风格指南。
3. 生成主线和章节大纲。
4. 将 bible、大纲、摘要、章节和场景索引进向量记忆。
5. 使用多 Agent 流程写章节：剧情架构师 → 连续性守门人 → 场景写手 → 文风润色编辑 → 终审批评家。
6. 对章节做一致性和文风审稿，保留完整 agent trace 方便人工复盘。
7. 在 Web UI 中打开项目、编辑 Markdown/YAML、索引记忆、触发多 Agent 写作并查看运行结果。

## 设计原则

- 人类作者保留最终控制权。
- 所有输出都保存为可读 Markdown/YAML。
- 默认不覆盖人工编辑过的章节。
- 复杂能力必须可追踪：多 Agent 每一步都写入 `runs/`。
- Web UI 先本地优先，明确标注本地文件系统和命令执行边界。
- 本地开发可低依赖运行；生产部署可升级到 OpenAI-compatible embeddings + pgvector。
- 用户可见文档默认中文；README 需要中英文双语，中文在前。

## 技术架构

- Python 3.11 + Typer CLI
- OpenAI-compatible chat completions
- OpenAI-compatible embeddings（可选）
- 本地 JSONL vector store（默认）
- Postgres + pgvector（可选生产后端）
- Pydantic 配置/状态模型
- Markdown/YAML 项目资产
- React / Next.js App Router Web UI
- shadcn/ui-style 组件 + Tailwind CSS
- Vercel AI SDK 数据流接口
- Zustand 前端状态管理
