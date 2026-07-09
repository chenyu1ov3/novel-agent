from typer.testing import CliRunner

from novel_agent.cli import app


runner = CliRunner()


def test_cli_help_shows_core_commands():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "init" in result.output
    assert "write" in result.output
    assert "review" in result.output


def test_init_command_creates_project(tmp_path):
    target = tmp_path / "demo"

    result = runner.invoke(app, ["init", str(target), "--title", "雪落长安", "--genre", "武侠"])

    assert result.exit_code == 0
    assert (target / "novel.yaml").exists()
    assert "雪落长安" in result.output
