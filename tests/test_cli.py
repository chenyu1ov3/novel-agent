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


def test_init_command_creates_project(tmp_path):
    target = tmp_path / "demo"

    result = runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])

    assert result.exit_code == 0
    assert (target / "novel.yaml").exists()
    assert (target / "summaries").is_dir()
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
