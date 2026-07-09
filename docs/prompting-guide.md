# Prompting Guide

## Rules

1. Prompts should be stored in `src/novel_agent/prompts/*.j2`, not hardcoded in Python.
2. Inputs should include project context, chapter goal, style guide, and constraints.
3. Outputs should be Markdown so users can edit and version-control results.
4. Ask the model not to overwrite established facts.
5. Require concrete scenes, actions, dialogue, and sensory details.

## Template Variables

Common variables:

- `title`
- `context`
- `chapter_number`
- `chapter_goal`
- `chapter_text`
- `style`

## Anti-patterns

- “随便发挥写一章” without constraints.
- Long hidden prompts inside Python code.
- Asking the model to rewrite user-edited files without confirmation.
