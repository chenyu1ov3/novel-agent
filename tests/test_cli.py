from typer.testing import CliRunner

from novel_agent.cli import app


runner = CliRunner()


def test_cli_help_shows_core_commands():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "init" in result.output
    assert "write" in result.output
    assert "review" in result.output
    assert "summarize" in result.output
    assert "continuity" in result.output
    assert "plan-scenes" in result.output
    assert "write-scene" in result.output
    assert "compose-chapter" in result.output
    assert "index-memory" in result.output
    assert "agent-run" in result.output


def test_init_command_creates_project(tmp_path):
    target = tmp_path / "demo"

    result = runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])

    assert result.exit_code == 0
    assert (target / "novel.yaml").exists()
    assert (target / "summaries").is_dir()
    assert (target / "scenes").is_dir()
    assert (target / "outlines" / "scenes").is_dir()
    assert "雪落长安" in result.output


def test_summarize_command_writes_summary_without_overwriting_existing_file(monkeypatch, tmp_path):
    target = tmp_path / "demo"
    runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])
    chapter_path = target / "chapters" / "ch001.md"
    chapter_path.write_text("# 第 1 章\n\n沈青在雪夜发现尸体。", encoding="utf-8")

    class FakeClient:
        def complete(self, system: str, user: str, *, temperature: float = 0.7) -> str:
            assert "沈青在雪夜发现尸体" in user
            return "# 第 1 章摘要\n\n沈青发现尸体。"

    monkeypatch.setattr("novel_agent.cli._client", lambda: FakeClient())

    first = runner.invoke(app, ["summarize", str(target), "--chapter", "1"])
    second = runner.invoke(app, ["summarize", str(target), "--chapter", "1"])

    assert first.exit_code == 0
    assert (target / "summaries" / "ch001.md").read_text(encoding="utf-8") == "# 第 1 章摘要\n\n沈青发现尸体。"
    assert second.exit_code != 0
    assert "already exists" in second.output


def test_summarize_command_supports_force_overwrite(monkeypatch, tmp_path):
    target = tmp_path / "demo"
    runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])
    (target / "chapters" / "ch001.md").write_text("# 第 1 章\n\n旧正文。", encoding="utf-8")
    summary_path = target / "summaries" / "ch001.md"
    summary_path.write_text("旧摘要", encoding="utf-8")

    class FakeClient:
        def complete(self, system: str, user: str, *, temperature: float = 0.7) -> str:
            return "新摘要"

    monkeypatch.setattr("novel_agent.cli._client", lambda: FakeClient())

    result = runner.invoke(app, ["summarize", str(target), "--chapter", "1", "--force"])

    assert result.exit_code == 0
    assert summary_path.read_text(encoding="utf-8") == "新摘要"


def test_write_command_includes_previous_summaries_only(monkeypatch, tmp_path):
    target = tmp_path / "demo"
    runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])
    (target / "summaries" / "ch001.md").write_text("第 1 章：沈青发现尸体。", encoding="utf-8")
    (target / "summaries" / "ch002.md").write_text("第 2 章：柳照夜找到铜牌。", encoding="utf-8")

    class FakeClient:
        def complete(self, system: str, user: str, *, temperature: float = 0.7) -> str:
            assert "沈青发现尸体" in user
            assert "柳照夜找到铜牌" not in user
            return "# 第 2 章\n\n正文。"

    monkeypatch.setattr("novel_agent.cli._client", lambda: FakeClient())

    result = runner.invoke(app, ["write", str(target), "--chapter", "2"])

    assert result.exit_code == 0


def test_continuity_command_writes_report(monkeypatch, tmp_path):
    target = tmp_path / "demo"
    runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])
    chapter_path = target / "chapters" / "ch001.md"
    chapter_path.write_text("# 第 1 章\n\n沈青在雪夜发现尸体。", encoding="utf-8")
    (target / "summaries" / "ch000.md").write_text("前情：玄灯旧案。", encoding="utf-8")

    class FakeClient:
        def complete(self, system: str, user: str, *, temperature: float = 0.7) -> str:
            assert "沈青在雪夜发现尸体" in user
            assert "人物一致性" in user
            return "# 第 1 章连续性检查\n\n## 总体结论\n\n无明显冲突。"

    monkeypatch.setattr("novel_agent.cli._client", lambda: FakeClient())

    result = runner.invoke(app, ["continuity", str(target), "--chapter", "1"])

    assert result.exit_code == 0
    report = target / "chapters" / "ch001.continuity.md"
    assert report.read_text(encoding="utf-8").startswith("# 第 1 章连续性检查")


def test_continuity_command_fails_when_chapter_missing(tmp_path):
    target = tmp_path / "demo"
    runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])

    result = runner.invoke(app, ["continuity", str(target), "--chapter", "1"])

    assert result.exit_code != 0
    assert "Chapter file does not exist" in result.output


def test_plan_scenes_command_writes_scene_outline(monkeypatch, tmp_path):
    target = tmp_path / "demo"
    runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])

    class FakeClient:
        def complete(self, system: str, user: str, *, temperature: float = 0.7) -> str:
            assert "场景规划" in user
            return "# 第 1 章场景规划\n\n## 场景 1\n- 目标：发现尸体"

    monkeypatch.setattr("novel_agent.cli._client", lambda: FakeClient())

    result = runner.invoke(app, ["plan-scenes", str(target), "--chapter", "1"])

    assert result.exit_code == 0
    assert (target / "outlines" / "scenes" / "ch001.md").read_text(encoding="utf-8").startswith("# 第 1 章场景规划")


def test_write_scene_command_writes_scene_without_overwriting_existing_file(monkeypatch, tmp_path):
    target = tmp_path / "demo"
    runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])
    (target / "outlines" / "scenes" / "ch001.md").write_text("# 第 1 章场景规划\n\n## 场景 1", encoding="utf-8")

    class FakeClient:
        def complete(self, system: str, user: str, *, temperature: float = 0.7) -> str:
            assert "场景 1" in user
            return "# 场景 1\n\n沈青踏入雪夜。"

    monkeypatch.setattr("novel_agent.cli._client", lambda: FakeClient())

    first = runner.invoke(app, ["write-scene", str(target), "--chapter", "1", "--scene", "1"])
    second = runner.invoke(app, ["write-scene", str(target), "--chapter", "1", "--scene", "1"])

    assert first.exit_code == 0
    assert (target / "scenes" / "ch001" / "s001.md").read_text(encoding="utf-8").startswith("# 场景 1")
    assert second.exit_code != 0
    assert "Scene already exists" in second.output


def test_compose_chapter_command_combines_scenes_without_overwriting_existing_chapter(tmp_path):
    target = tmp_path / "demo"
    runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])
    scene_dir = target / "scenes" / "ch001"
    scene_dir.mkdir(parents=True)
    (scene_dir / "s002.md").write_text("# 场景 2\n\n后发生。", encoding="utf-8")
    (scene_dir / "s001.md").write_text("# 场景 1\n\n先发生。", encoding="utf-8")

    first = runner.invoke(app, ["compose-chapter", str(target), "--chapter", "1"])
    second = runner.invoke(app, ["compose-chapter", str(target), "--chapter", "1"])

    assert first.exit_code == 0
    text = (target / "chapters" / "ch001.md").read_text(encoding="utf-8")
    assert text.index("先发生") < text.index("后发生")
    assert second.exit_code != 0
    assert "Chapter already exists" in second.output


def test_compose_chapter_command_supports_force_overwrite(tmp_path):
    target = tmp_path / "demo"
    runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])
    chapter_path = target / "chapters" / "ch001.md"
    chapter_path.write_text("旧章节", encoding="utf-8")
    scene_dir = target / "scenes" / "ch001"
    scene_dir.mkdir(parents=True)
    (scene_dir / "s001.md").write_text("# 场景 1\n\n新章节。", encoding="utf-8")

    result = runner.invoke(app, ["compose-chapter", str(target), "--chapter", "1", "--force"])

    assert result.exit_code == 0
    assert "新章节" in chapter_path.read_text(encoding="utf-8")


def test_index_memory_command_builds_local_vector_index(tmp_path):
    target = tmp_path / "demo"
    runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])
    (target / "bible" / "characters.md").write_text("# Characters\n\n沈青有一枚铜铃。", encoding="utf-8")

    result = runner.invoke(app, ["index-memory", str(target)])

    assert result.exit_code == 0
    assert (target / "memory" / "vectors.jsonl").exists()
    assert "Indexed" in result.output


def test_agent_run_command_writes_chapter_and_trace(monkeypatch, tmp_path):
    target = tmp_path / "demo"
    runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])
    (target / "bible" / "characters.md").write_text("# Characters\n\n沈青有一枚铜铃。", encoding="utf-8")
    runner.invoke(app, ["index-memory", str(target)])

    class FakeClient:
        def complete(self, system: str, user: str, *, temperature: float = 0.7) -> str:
            if "文风润色编辑" in system:
                return "# 第 1 章\n\n沈青拾起铜铃。"
            if "终审批评家" in system:
                return "终审通过。"
            return "中间结果：铜铃线索。"

    monkeypatch.setattr("novel_agent.cli._client", lambda: FakeClient())

    result = runner.invoke(app, ["agent-run", str(target), "--chapter", "1", "--goal", "发现铜铃"])

    assert result.exit_code == 0
    assert "沈青拾起铜铃" in (target / "chapters" / "ch001.md").read_text(encoding="utf-8")
    traces = list((target / "runs").glob("ch001-*.md"))
    assert traces
    assert "终审通过" in traces[0].read_text(encoding="utf-8")
