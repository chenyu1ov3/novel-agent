from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from novel_agent.models import NovelConfig


BIBLE_FILES = {
    "premise.md": "# Premise\n\n一句话梗概、主题、卖点。\n",
    "world.md": "# World\n\n世界观、地点、规则、限制。\n",
    "characters.md": "# Characters\n\n主要角色卡、目标、秘密、说话方式。\n",
    "timeline.md": "# Timeline\n\n重要事件时间线。\n",
    "style.md": "# Style Guide\n\n文风、视角、节奏、禁忌。\n",
}


@dataclass(frozen=True)
class NovelProject:
    root: Path
    config: NovelConfig

    @classmethod
    def init(
        cls,
        root: str | Path,
        *,
        title: str,
        genre: str = "未设定",
        language: str = "zh-CN",
        target_words: int = 100_000,
        pov: str = "第三人称有限视角",
        style: str = "清晰、有画面感、避免空泛AI腔",
    ) -> "NovelProject":
        project_root = Path(root).expanduser().resolve()
        project_root.mkdir(parents=True, exist_ok=True)
        (project_root / "bible").mkdir(exist_ok=True)
        (project_root / "outlines").mkdir(exist_ok=True)
        (project_root / "chapters").mkdir(exist_ok=True)
        (project_root / "summaries").mkdir(exist_ok=True)

        config = NovelConfig(
            title=title,
            genre=genre,
            language=language,
            target_words=target_words,
            pov=pov,
            style=style,
        )
        cls._write_yaml(project_root / "novel.yaml", config.model_dump())

        for filename, content in BIBLE_FILES.items():
            cls._write_if_missing(project_root / "bible" / filename, content)
        cls._write_if_missing(
            project_root / "outlines" / "arc.md",
            "# Story Arc\n\n主线、分卷、核心冲突。\n",
        )
        cls._write_if_missing(
            project_root / "outlines" / "chapters.md",
            "# Chapter Outline\n\n- [ ] 第 1 章：开端\n",
        )
        cls._write_if_missing(
            project_root / "README.md",
            f"# {title}\n\n由 novel-agent 管理的小说项目。\n",
        )
        return cls(project_root, config)

    @classmethod
    def load(cls, root: str | Path) -> "NovelProject":
        project_root = Path(root).expanduser().resolve()
        config_path = project_root / "novel.yaml"
        if not config_path.exists():
            raise FileNotFoundError(f"Not a novel-agent project: {project_root}")
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        return cls(project_root, NovelConfig.model_validate(data))

    def chapter_path(self, number: int, *, suffix: str = ".md") -> Path:
        return self.root / "chapters" / f"ch{number:03d}{suffix}"

    def summary_path(self, number: int) -> Path:
        return self.root / "summaries" / f"ch{number:03d}.md"

    def read_summaries(self, *, before_chapter: int | None = None) -> str:
        summary_dir = self.root / "summaries"
        if not summary_dir.exists():
            return ""

        parts: list[str] = []
        for path in sorted(summary_dir.glob("ch*.md")):
            chapter_number = self._chapter_number_from_path(path)
            if chapter_number is None:
                continue
            if before_chapter is not None and chapter_number >= before_chapter:
                continue
            relative = path.relative_to(self.root).as_posix()
            parts.append(f"## {relative}\n\n{path.read_text(encoding='utf-8')}")
        return "\n\n".join(parts)

    def read_context(self, *, before_chapter: int | None = None) -> str:
        parts: list[str] = []
        for relative in [
            "novel.yaml",
            "bible/premise.md",
            "bible/world.md",
            "bible/characters.md",
            "bible/timeline.md",
            "bible/style.md",
            "outlines/arc.md",
            "outlines/chapters.md",
        ]:
            path = self.root / relative
            if path.exists():
                parts.append(f"## {relative}\n\n{path.read_text(encoding='utf-8')}")
        summaries = self.read_summaries(before_chapter=before_chapter)
        if summaries:
            parts.append(f"# Chapter Summaries\n\n{summaries}")
        return "\n\n".join(parts)

    @staticmethod
    def _chapter_number_from_path(path: Path) -> int | None:
        stem = path.stem
        if not stem.startswith("ch"):
            return None
        try:
            return int(stem[2:])
        except ValueError:
            return None

    @staticmethod
    def _write_if_missing(path: Path, content: str) -> None:
        if not path.exists():
            path.write_text(content, encoding="utf-8")

    @staticmethod
    def _write_yaml(path: Path, data: dict[str, Any]) -> None:
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
