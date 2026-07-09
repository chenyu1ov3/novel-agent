from novel_agent.agents import MultiAgentOrchestrator, default_agent_registry
from novel_agent.project import NovelProject
from novel_agent.vector_store import HashEmbeddingProvider, LocalVectorStore, RetrievalEngine


class FakeClient:
    def __init__(self):
        self.calls: list[tuple[str, str, float]] = []

    def complete(self, system: str, user: str, *, temperature: float = 0.7) -> str:
        self.calls.append((system, user, temperature))
        if "首席剧情架构师" in system:
            return "剧情架构：沈青发现铜铃并决定追查玄灯旧案。"
        if "连续性守门人" in system:
            return "连续性约束：铜铃必须保持为玄灯旧案线索。"
        if "场景写手" in system:
            return "# 第 1 章草稿\n\n沈青在雪夜拾起铜铃。"
        if "文风润色编辑" in system:
            return "# 第 1 章润色稿\n\n沈青在雪夜拾起那枚铜铃。"
        if "终审批评家" in system:
            return "终审：节奏清晰，可进入人工修改。"
        return "未知输出"


def test_multi_agent_orchestrator_runs_default_agents_with_retrieved_memory(tmp_path):
    project = NovelProject.init(tmp_path / "demo", title="雪落长安", genre="武侠")
    (project.root / "bible" / "characters.md").write_text(
        "# Characters\n\n沈青随身带着一枚铜铃。",
        encoding="utf-8",
    )
    embeddings = HashEmbeddingProvider(dimensions=32)
    store = LocalVectorStore(dimensions=32)
    store.index_project(project, embeddings)
    retrieval = RetrievalEngine(store=store, embeddings=embeddings)
    client = FakeClient()

    result = MultiAgentOrchestrator(
        project=project,
        client=client,
        registry=default_agent_registry(),
        retrieval=retrieval,
    ).draft_chapter(chapter=1, goal="发现铜铃")

    assert [step.agent_id for step in result.steps] == [
        "story_architect",
        "continuity_guardian",
        "scene_writer",
        "style_editor",
        "critic",
    ]
    assert "铜铃" in client.calls[0][1]
    assert "检索记忆" in client.calls[2][1]
    assert result.final_text.startswith("# 第 1 章润色稿")
    assert "终审：节奏清晰" in result.review
