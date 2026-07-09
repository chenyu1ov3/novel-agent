from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from novel_agent.agents import MultiAgentOrchestrator
from novel_agent.config import get_settings
from novel_agent.llm import LLMClient
from novel_agent.project import NovelProject
from novel_agent.prompting import render_prompt
from novel_agent.vector_store import (
    EmbeddingProvider,
    HashEmbeddingProvider,
    LocalVectorStore,
    OpenAIEmbeddingProvider,
    PgVectorStore,
    RetrievalEngine,
)

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


def _embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    if settings.novel_agent_embedding_model:
        api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
        return OpenAIEmbeddingProvider(
            model=settings.novel_agent_embedding_model,
            dimensions=settings.novel_agent_embedding_dimensions,
            api_key=api_key,
            base_url=settings.openai_base_url,
        )
    return HashEmbeddingProvider(dimensions=settings.novel_agent_embedding_dimensions)


def _local_retrieval(project: NovelProject) -> RetrievalEngine:
    embeddings = _embedding_provider()
    store = LocalVectorStore(dimensions=embeddings.dimensions, persist_path=project.local_vector_path())
    return RetrievalEngine(store=store, embeddings=embeddings)


def _pgvector_unavailable_error() -> typer.BadParameter:
    return typer.BadParameter(
        "pgvector requires psycopg. Install with: pip install -e '.[pgvector]'"
    )


def _open_pgvector_store(project: NovelProject) -> PgVectorStore:
    settings = get_settings()
    if settings.novel_agent_pgvector_dsn is None:
        raise typer.BadParameter("NOVEL_AGENT_PGVECTOR_DSN is required for --backend pgvector")
    try:
        import psycopg  # type: ignore[import-not-found]
    except ImportError as exc:
        raise _pgvector_unavailable_error() from exc
    connection = psycopg.connect(settings.novel_agent_pgvector_dsn.get_secret_value())
    table_name = settings.novel_agent_pgvector_table or project.config.memory.pgvector_table
    return PgVectorStore(
        connection=connection,
        table_name=table_name,
        dimensions=_embedding_provider().dimensions,
    )


def _write_output(target: Path, text: str, *, force: bool, exists_message: str) -> None:
    if target.exists() and not force:
        raise typer.BadParameter(exists_message)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


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
        context=project.read_context(before_chapter=chapter),
        style=project.config.style,
    )
    text = _client().complete(system="你是专业中文小说作者。", user=prompt, temperature=0.85)
    target.write_text(text, encoding="utf-8")
    console.print(f"[green]Wrote[/green] {target}")


@app.command()
def summarize(
    path: Annotated[Path, typer.Argument(help="Novel project directory.")],
    chapter: Annotated[int, typer.Option("--chapter", "-c", help="Chapter number.")] = 1,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing summary file.")] = False,
) -> None:
    """Summarize a chapter into reusable long-form memory."""

    project = NovelProject.load(path)
    chapter_path = project.chapter_path(chapter)
    if not chapter_path.exists():
        raise typer.BadParameter(f"Chapter file does not exist: {chapter_path}")
    target = project.summary_path(chapter)
    if target.exists() and not force:
        raise typer.BadParameter(f"Summary already exists: {target}. Use --force to overwrite.")
    prompt = render_prompt(
        "summarize.j2",
        title=project.config.title,
        chapter_number=chapter,
        context=project.read_context(before_chapter=chapter),
        chapter_text=chapter_path.read_text(encoding="utf-8"),
    )
    text = _client().complete(system="你是长篇小说的剧情记录员。", user=prompt, temperature=0.2)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    console.print(f"[green]Wrote[/green] {target}")


@app.command()
def continuity(
    path: Annotated[Path, typer.Argument(help="Novel project directory.")],
    chapter: Annotated[int, typer.Option("--chapter", "-c", help="Chapter number.")] = 1,
) -> None:
    """Check a chapter for continuity issues against the project context."""

    project = NovelProject.load(path)
    chapter_path = project.chapter_path(chapter)
    if not chapter_path.exists():
        raise typer.BadParameter(f"Chapter file does not exist: {chapter_path}")
    prompt = render_prompt(
        "continuity.j2",
        title=project.config.title,
        chapter_number=chapter,
        context=project.read_context(before_chapter=chapter),
        chapter_text=chapter_path.read_text(encoding="utf-8"),
    )
    text = _client().complete(system="你是严格的长篇小说连续性编辑。", user=prompt, temperature=0.2)
    target = project.chapter_path(chapter, suffix=".continuity.md")
    target.write_text(text, encoding="utf-8")
    console.print(f"[green]Wrote[/green] {target}")


@app.command("plan-scenes")
def plan_scenes(
    path: Annotated[Path, typer.Argument(help="Novel project directory.")],
    chapter: Annotated[int, typer.Option("--chapter", "-c", help="Chapter number.")] = 1,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing scene outline.")] = False,
) -> None:
    """Plan scenes for one chapter."""

    project = NovelProject.load(path)
    target = project.scene_outline_path(chapter)
    if target.exists() and not force:
        raise typer.BadParameter(f"Scene outline already exists: {target}. Use --force to overwrite.")
    prompt = render_prompt(
        "plan_scenes.j2",
        title=project.config.title,
        chapter_number=chapter,
        context=project.read_context(before_chapter=chapter),
    )
    text = _client().complete(system="你是长篇小说结构编辑。", user=prompt, temperature=0.5)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    console.print(f"[green]Wrote[/green] {target}")


@app.command("write-scene")
def write_scene(
    path: Annotated[Path, typer.Argument(help="Novel project directory.")],
    chapter: Annotated[int, typer.Option("--chapter", "-c", help="Chapter number.")] = 1,
    scene: Annotated[int, typer.Option("--scene", "-s", help="Scene number.")] = 1,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing scene draft.")] = False,
) -> None:
    """Write one scene draft for a chapter."""

    project = NovelProject.load(path)
    target = project.scene_path(chapter, scene)
    if target.exists() and not force:
        raise typer.BadParameter(f"Scene already exists: {target}. Use --force to overwrite.")
    scene_outline_path = project.scene_outline_path(chapter)
    scene_outline = scene_outline_path.read_text(encoding="utf-8") if scene_outline_path.exists() else ""
    prompt = render_prompt(
        "write_scene.j2",
        title=project.config.title,
        chapter_number=chapter,
        scene_number=scene,
        context=project.read_context(before_chapter=chapter),
        scene_outline=scene_outline,
        style=project.config.style,
    )
    text = _client().complete(system="你是专业中文小说作者。", user=prompt, temperature=0.85)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    console.print(f"[green]Wrote[/green] {target}")


@app.command("compose-chapter")
def compose_chapter(
    path: Annotated[Path, typer.Argument(help="Novel project directory.")],
    chapter: Annotated[int, typer.Option("--chapter", "-c", help="Chapter number.")] = 1,
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing chapter file.")] = False,
) -> None:
    """Compose scene drafts into a chapter file."""

    project = NovelProject.load(path)
    target = project.chapter_path(chapter)
    if target.exists() and not force:
        raise typer.BadParameter(f"Chapter already exists: {target}. Use --force to overwrite.")
    text = project.read_scene_drafts(chapter)
    if not text:
        raise typer.BadParameter(f"No scene drafts found for chapter {chapter}.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    console.print(f"[green]Wrote[/green] {target}")


@app.command("agent-run")
def agent_run(
    path: Annotated[Path, typer.Argument(help="Novel project directory.")],
    chapter: Annotated[int, typer.Option("--chapter", "-c", help="Chapter number.")] = 1,
    goal: Annotated[str, typer.Option("--goal", help="Chapter-specific goal.")] = "按章节大纲推进剧情",
    force: Annotated[bool, typer.Option("--force", help="Overwrite existing chapter file.")] = False,
    use_retrieval: Annotated[
        bool,
        typer.Option("--retrieval/--no-retrieval", help="Use indexed vector memory when available."),
    ] = True,
) -> None:
    """Draft a chapter through the planner/continuity/writer/editor/critic agent pipeline."""

    project = NovelProject.load(path)
    target = project.chapter_path(chapter)
    if target.exists() and not force:
        target = project.chapter_path(chapter, suffix=".draft.md")
    retrieval = _local_retrieval(project) if use_retrieval else None
    orchestrator = MultiAgentOrchestrator(
        project=project,
        client=_client(),
        retrieval=retrieval,
    )
    result = orchestrator.draft_chapter(chapter=chapter, goal=goal)
    _write_output(
        target,
        result.final_text,
        force=True,
        exists_message=f"Chapter already exists: {target}.",
    )
    trace_path = orchestrator.save_run(result)
    console.print(
        f"[green]Wrote[/green] {target} and {trace_path} ({len(result.steps)} agent steps)"
    )


@app.command("index-memory")
def index_memory(
    path: Annotated[Path, typer.Argument(help="Novel project directory.")],
    backend: Annotated[str, typer.Option("--backend", help="Vector backend: local or pgvector.")] = "local",
) -> None:
    """Index project bible/outlines/chapters into vector memory."""

    project = NovelProject.load(path)
    embeddings = _embedding_provider()
    if backend == "pgvector":
        store = _open_pgvector_store(project)
        store.ensure_schema()
        count = store.index_project(project, embeddings)
        console.print(
            f"[green]Indexed[/green] {count} memory chunks into pgvector table {store.table_name}"
        )
        return
    if backend != "local":
        raise typer.BadParameter("backend must be 'local' or 'pgvector'")
    local_store = LocalVectorStore(dimensions=embeddings.dimensions, persist_path=project.local_vector_path())
    count = local_store.index_project(project, embeddings)
    console.print(f"[green]Indexed[/green] {count} memory chunks into {project.local_vector_path()}")


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
