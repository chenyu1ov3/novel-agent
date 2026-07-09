from __future__ import annotations

from importlib.resources import files
from typing import Any

from jinja2 import Environment, StrictUndefined


def render_prompt(template_name: str, **context: Any) -> str:
    """Render a packaged Jinja2 prompt template."""

    template_path = files("novel_agent").joinpath("prompts", template_name)
    if not template_path.is_file():
        raise FileNotFoundError(f"Prompt template not found: {template_name}")
    env = Environment(autoescape=False, undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    template = env.from_string(template_path.read_text(encoding="utf-8"))
    return template.render(**context)
