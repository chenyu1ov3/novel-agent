from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from novel_agent.config import get_settings
from novel_agent.llm import LLMClient
from novel_agent.project import NovelProject
from novel_agent.prompting import render_prompt

app = typer.Typer(help="AI-assisted long-form novel writing agent.")
console = Console()


def _client() -> LLMClient:
    settings = get_settings()
    api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
    return LLMClient(
        model=settings.novel_agent_model,
        api_key=api_key,
        base_url=settings.openai_base_url,
    )


@app.command()
def init(
    path: Annotated[Path, typer.Argument(help="Directory for the novel project.")],
    title: Annotated[str, typer.Option("--title", "-t", help="Novel title.")] = "未命名小说",
    genre: Annotated[str, typer.Option("--genre", "-g", help="Novel genre.")] = "未设定",
    language: Annotated[str, typer.Option("--language", help="Project language.")] = "zh-CN",
    target_words: Annotated[int, typer.Option("--target-words", help="Target word count.")] = 100_000,
) -> None:
    """Initialize a new novel project."""

    project = NovelProject.init(
        path,
        title=title,
        genre=genre,
        language=language,
        target_words=target_words,
    )
    console.print(f"[green]Initialized[/green] {project.config.title}: {project.root}")


@app.command()
def brainstorm(
    path: Annotated[Path, typer.Argument(help="Novel project directory.")],
    idea: Annotated[str, typer.Option("--idea", "-i", help="Seed idea for the story.")],
    output: Annotated[str, typer.Option("--output", "-o", help="Relative output file.")] = "bible/premise.md",
) -> None:
    """Generate a story premise and initial bible notes."""

    project = NovelProject.load(path)
    prompt = render_prompt("brainstorm.j2", title=project.config.title, idea=idea)
    text = _client().complete(system="你是专业小说策划。", user=prompt, temperature=0.8)
    target = project.root / output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    console.print(f"[green]Wrote[/green] {target}")


@app.command()
def outline(
    path: Annotated[Path, typer.Argument(help="Novel project directory.")],
    output: Annotated[str, typer.Option("--output", "-o", help="Relative output file.")] = "outlines/chapters.md",
) -> None:
    """Generate or refresh the chapter outline."""

    project = NovelProject.load(path)
    prompt = render_prompt("outline.j2", title=project.config.title, context=project.read_context())
    text = _client().complete(system="你是长篇小说结构编辑。", user=prompt, temperature=0.7)
    target = project.root / output
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    console.print(f"[green]Wrote[/green] {target}")


@app.command()
def write(
    path: Annotated[Path, typer.Argument(help="Novel project directory.")],
    chapter: Annotated[int, typer.Option("--chapter", "-c", help="Chapter number.")] = 1,
    goal: Annotated[str, typer.Option("--goal", help="Chapter-specific goal.")] = "按章节大纲推进剧情",
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing chapter file.")] = False,
) -> None:
    """Write a chapter draft from the project bible and outline."""

    project = NovelProject.load(path)
    target = project.chapter_path(chapter)
    if target.exists() and not force:
        target = project.chapter_path(chapter, suffix=".draft.md")
    prompt = render_prompt(
        "chapter_write.j2",
        title=project.config.title,
        chapter_number=chapter,
        chapter_goal=goal,
        context=project.read_context(),
        style=project.config.style,
    )
    text = _client().complete(system="你是专业中文小说作者。", user=prompt, temperature=0.85)
    target.write_text(text, encoding="utf-8")
    console.print(f"[green]Wrote[/green] {target}")


@app.command()
def review(
    path: Annotated[Path, typer.Argument(help="Novel project directory.")],
    chapter: Annotated[int, typer.Option("--chapter", "-c", help="Chapter number.")] = 1,
) -> None:
    """Review a chapter for consistency, style, and execution."""

    project = NovelProject.load(path)
    chapter_path = project.chapter_path(chapter)
    if not chapter_path.exists():
        raise typer.BadParameter(f"Chapter file does not exist: {chapter_path}")
    prompt = render_prompt(
        "review.j2",
        title=project.config.title,
        chapter_number=chapter,
        context=project.read_context(),
        chapter_text=chapter_path.read_text(encoding="utf-8"),
    )
    text = _client().complete(system="你是严格的小说审稿编辑。", user=prompt, temperature=0.3)
    target = project.chapter_path(chapter, suffix=".review.md")
    target.write_text(text, encoding="utf-8")
    console.print(f"[green]Wrote[/green] {target}")


if __name__ == "__main__":
    app()
