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
