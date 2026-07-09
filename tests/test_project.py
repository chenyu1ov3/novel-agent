from pathlib import Path

import yaml

from novel_agent.project import NovelProject


def test_init_creates_expected_project_structure(tmp_path: Path):
    target = tmp_path / "my-novel"

    project = NovelProject.init(target, title="镜中城", genre="悬疑")

    assert project.root == target
    assert (target / "novel.yaml").exists()
    assert (target / "bible" / "premise.md").exists()
    assert (target / "bible" / "world.md").exists()
    assert (target / "bible" / "characters.md").exists()
    assert (target / "bible" / "timeline.md").exists()
    assert (target / "bible" / "style.md").exists()
    assert (target / "outlines" / "chapters.md").exists()
    assert (target / "chapters").is_dir()
    assert (target / "summaries").is_dir()

    data = yaml.safe_load((target / "novel.yaml").read_text(encoding="utf-8"))
    assert data["title"] == "镜中城"
    assert data["genre"] == "悬疑"


def test_load_reads_existing_project_config(tmp_path: Path):
    target = tmp_path / "my-novel"
    NovelProject.init(target, title="星海旧约", genre="科幻")

    project = NovelProject.load(target)

    assert project.config.title == "星海旧约"
    assert project.config.genre == "科幻"


def test_chapter_path_uses_zero_padded_numbers(tmp_path: Path):
    target = tmp_path / "my-novel"
    project = NovelProject.init(target, title="星海旧约")

    assert project.chapter_path(7) == target / "chapters" / "ch007.md"


def test_summary_path_uses_zero_padded_numbers(tmp_path: Path):
    target = tmp_path / "my-novel"
    project = NovelProject.init(target, title="星海旧约")

    assert project.summary_path(7) == target / "summaries" / "ch007.md"


def test_read_summaries_returns_previous_chapters_in_order(tmp_path: Path):
    target = tmp_path / "my-novel"
    project = NovelProject.init(target, title="星海旧约")
    project.summary_path(1).write_text("# 第 1 章摘要\n\n主角离开故乡。", encoding="utf-8")
    project.summary_path(2).write_text("# 第 2 章摘要\n\n主角抵达边城。", encoding="utf-8")
    project.summary_path(3).write_text("# 第 3 章摘要\n\n主角遇到旧敌。", encoding="utf-8")

    summaries = project.read_summaries(before_chapter=3)

    assert "## summaries/ch001.md" in summaries
    assert "主角离开故乡" in summaries
    assert "## summaries/ch002.md" in summaries
    assert "主角抵达边城" in summaries
    assert "主角遇到旧敌" not in summaries


def test_read_context_includes_previous_summaries_for_target_chapter(tmp_path: Path):
    target = tmp_path / "my-novel"
    project = NovelProject.init(target, title="星海旧约")
    project.summary_path(1).write_text("# 第 1 章摘要\n\n主角获得星图。", encoding="utf-8")

    context = project.read_context(before_chapter=2)

    assert "主角获得星图" in context
