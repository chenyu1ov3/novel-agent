from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from novel_agent.llm import LLMClient
from novel_agent.project import NovelProject
from novel_agent.vector_store import RetrievalEngine

AgentId = Literal[
    "story_architect",
    "continuity_guardian",
    "scene_writer",
    "style_editor",
    "critic",
]


class AgentSpec(BaseModel):
    """Declarative role configuration for a writing agent."""

    agent_id: AgentId
    title: str
    system_prompt: str
    temperature: float = 0.5
    responsibilities: list[str] = Field(default_factory=list)


class AgentStep(BaseModel):
    """One completed agent turn in a multi-agent run."""

    agent_id: AgentId
    title: str
    prompt: str
    output: str


class MultiAgentRunResult(BaseModel):
    """Structured result of a chapter-drafting agent pipeline."""

    chapter: int
    goal: str
    final_text: str
    review: str
    steps: list[AgentStep]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_markdown(self) -> str:
        parts = [
            f"# Multi-Agent Run: Chapter {self.chapter:03d}",
            "",
            f"- Goal: {self.goal}",
            f"- Created at: {self.created_at.isoformat()}",
            "",
            "## Final Draft",
            "",
            self.final_text,
            "",
            "## Critic Review",
            "",
            self.review,
            "",
            "## Agent Trace",
        ]
        for step in self.steps:
            parts.extend(["", f"### {step.title} (`{step.agent_id}`)", "", step.output])
        return "\n".join(parts).rstrip() + "\n"


@dataclass(frozen=True)
class AgentRegistry:
    """Registry that keeps the orchestrator independent from concrete roles."""

    agents: tuple[AgentSpec, ...]

    def by_id(self, agent_id: AgentId) -> AgentSpec:
        for agent in self.agents:
            if agent.agent_id == agent_id:
                return agent
        raise KeyError(agent_id)


class MultiAgentOrchestrator:
    """Coordinates planner, continuity, writer, editor, and critic agents."""

    def __init__(
        self,
        *,
        project: NovelProject,
        client: LLMClient,
        registry: AgentRegistry | None = None,
        retrieval: RetrievalEngine | None = None,
    ) -> None:
        self.project = project
        self.client = client
        self.registry = registry or default_agent_registry()
        self.retrieval = retrieval

    def draft_chapter(self, *, chapter: int, goal: str) -> MultiAgentRunResult:
        context = self.project.read_context(before_chapter=chapter)
        retrieved = self._retrieved_context(goal)
        steps: list[AgentStep] = []

        architecture = self._run_agent(
            "story_architect",
            _story_architect_prompt(
                title=self.project.config.title,
                chapter=chapter,
                goal=goal,
                context=context,
                retrieved=retrieved,
            ),
            steps,
        )
        continuity = self._run_agent(
            "continuity_guardian",
            _continuity_prompt(
                title=self.project.config.title,
                chapter=chapter,
                goal=goal,
                context=context,
                retrieved=retrieved,
                architecture=architecture,
            ),
            steps,
        )
        draft = self._run_agent(
            "scene_writer",
            _scene_writer_prompt(
                title=self.project.config.title,
                chapter=chapter,
                goal=goal,
                context=context,
                retrieved=retrieved,
                architecture=architecture,
                continuity=continuity,
                style=self.project.config.style,
            ),
            steps,
        )
        final_text = self._run_agent(
            "style_editor",
            _style_editor_prompt(
                title=self.project.config.title,
                chapter=chapter,
                style=self.project.config.style,
                continuity=continuity,
                draft=draft,
            ),
            steps,
        )
        review = self._run_agent(
            "critic",
            _critic_prompt(
                title=self.project.config.title,
                chapter=chapter,
                goal=goal,
                context=context,
                retrieved=retrieved,
                final_text=final_text,
            ),
            steps,
        )

        return MultiAgentRunResult(
            chapter=chapter,
            goal=goal,
            final_text=final_text,
            review=review,
            steps=steps,
        )

    def save_run(self, result: MultiAgentRunResult) -> Path:
        self.project.runs_dir.mkdir(parents=True, exist_ok=True)
        timestamp = result.created_at.strftime("%Y%m%d-%H%M%S")
        markdown_path = self.project.runs_dir / f"ch{result.chapter:03d}-{timestamp}.md"
        json_path = self.project.runs_dir / f"ch{result.chapter:03d}-{timestamp}.json"
        markdown_path.write_text(result.to_markdown(), encoding="utf-8")
        json_path.write_text(json.dumps(result.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
        return markdown_path

    def _run_agent(self, agent_id: AgentId, prompt: str, steps: list[AgentStep]) -> str:
        spec = self.registry.by_id(agent_id)
        output = self.client.complete(system=spec.system_prompt, user=prompt, temperature=spec.temperature)
        steps.append(AgentStep(agent_id=agent_id, title=spec.title, prompt=prompt, output=output))
        return output

    def _retrieved_context(self, goal: str) -> str:
        if self.retrieval is None:
            return ""
        query = f"{self.project.config.title}\n{goal}"
        return self.retrieval.context_block(query, limit=8)


def default_agent_registry() -> AgentRegistry:
    return AgentRegistry(
        agents=(
            AgentSpec(
                agent_id="story_architect",
                title="剧情架构师",
                system_prompt="你是首席剧情架构师，负责把长篇小说目标拆成因果清晰、可执行的章节策略。",
                temperature=0.45,
                responsibilities=["章节目标", "冲突升级", "场景因果", "悬念钩子"],
            ),
            AgentSpec(
                agent_id="continuity_guardian",
                title="连续性守门人",
                system_prompt="你是连续性守门人，专门防止人物动机、时间线、世界观和伏笔前后冲突。",
                temperature=0.2,
                responsibilities=["人物一致性", "时间线", "世界观规则", "伏笔账本"],
            ),
            AgentSpec(
                agent_id="scene_writer",
                title="场景写手",
                system_prompt="你是场景写手，负责写具体动作、对白、感官细节和情绪推进，避免空泛总结腔。",
                temperature=0.82,
                responsibilities=["正文草稿", "对白", "动作", "情绪节奏"],
            ),
            AgentSpec(
                agent_id="style_editor",
                title="文风润色编辑",
                system_prompt="你是文风润色编辑，负责在不改事实的前提下统一语气、节奏和画面感。",
                temperature=0.35,
                responsibilities=["文风统一", "删空话", "节奏修订"],
            ),
            AgentSpec(
                agent_id="critic",
                title="终审批评家",
                system_prompt="你是终审批评家，必须严格指出草稿能否进入人工修改，以及还缺什么。",
                temperature=0.25,
                responsibilities=["质量门禁", "风险提示", "修改清单"],
            ),
        )
    )


def _story_architect_prompt(*, title: str, chapter: int, goal: str, context: str, retrieved: str) -> str:
    return f"""请为《{title}》第 {chapter} 章制定写作蓝图。

## 本章目标
{goal}

## 项目上下文
{context}

## 检索记忆
{retrieved or '（未启用向量检索或暂无命中）'}

输出 Markdown，包含：章节承诺、3-6 个关键场景、每个场景的因果作用、结尾钩子、禁止触碰的设定边界。
"""


def _continuity_prompt(
    *, title: str, chapter: int, goal: str, context: str, retrieved: str, architecture: str
) -> str:
    return f"""请审查《{title}》第 {chapter} 章蓝图的连续性风险。

## 本章目标
{goal}

## 项目上下文
{context}

## 检索记忆
{retrieved or '（未启用向量检索或暂无命中）'}

## 剧情架构师蓝图
{architecture}

输出 Markdown：必须保留的事实、人物动机约束、时间线约束、伏笔/线索约束、高风险冲突与规避方式。
"""


def _scene_writer_prompt(
    *,
    title: str,
    chapter: int,
    goal: str,
    context: str,
    retrieved: str,
    architecture: str,
    continuity: str,
    style: str,
) -> str:
    return f"""请为《{title}》第 {chapter} 章写完整章节草稿。

## 本章目标
{goal}

## 项目上下文
{context}

## 检索记忆
{retrieved or '（未启用向量检索或暂无命中）'}

## 剧情架构
{architecture}

## 连续性约束
{continuity}

## 文风要求
{style}

要求：输出 Markdown 正文；写具体动作、对白、环境与情绪变化；不得推翻连续性约束；结尾保留可追读钩子。
"""


def _style_editor_prompt(*, title: str, chapter: int, style: str, continuity: str, draft: str) -> str:
    return f"""请润色《{title}》第 {chapter} 章草稿。

## 文风要求
{style}

## 不可改动的连续性约束
{continuity}

## 草稿
{draft}

要求：只输出润色后的完整 Markdown 正文；保持事实不变；删除空泛 AI 腔；增强动作、对白和画面感。
"""


def _critic_prompt(
    *, title: str, chapter: int, goal: str, context: str, retrieved: str, final_text: str
) -> str:
    return f"""请终审《{title}》第 {chapter} 章。

## 本章目标
{goal}

## 项目上下文
{context}

## 检索记忆
{retrieved or '（未启用向量检索或暂无命中）'}

## 终稿
{final_text}

输出 Markdown：总体结论、是否达成本章目标、连续性风险、文风问题、必须修改项、可选优化项。
"""
