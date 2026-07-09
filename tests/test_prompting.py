from novel_agent.prompting import render_prompt


def test_render_prompt_uses_packaged_template():
    output = render_prompt("chapter_write.j2", title="试写", chapter_number=1, chapter_goal="主角发现线索", context="暂无", style="克制、悬疑")

    assert "试写" in output
    assert "第 1 章" in output
    assert "主角发现线索" in output


def test_render_summarize_prompt_includes_chapter_text():
    output = render_prompt(
        "summarize.j2",
        title="雪落长安",
        chapter_number=1,
        context="角色：沈青",
        chapter_text="沈青在雪夜发现尸体。",
    )

    assert "雪落长安" in output
    assert "第 1 章" in output
    assert "沈青在雪夜发现尸体" in output


def test_render_continuity_prompt_includes_required_sections():
    output = render_prompt(
        "continuity.j2",
        title="雪落长安",
        chapter_number=1,
        context="角色：沈青",
        chapter_text="沈青在雪夜发现尸体。",
    )

    assert "雪落长安" in output
    assert "第 1 章" in output
    assert "人物一致性" in output
    assert "时间线冲突" in output
    assert "设定冲突" in output
    assert "沈青在雪夜发现尸体" in output


def test_render_scene_prompts_include_scene_context():
    plan_output = render_prompt(
        "plan_scenes.j2",
        title="雪落长安",
        chapter_number=1,
        context="本章目标：发现尸体",
    )
    write_output = render_prompt(
        "write_scene.j2",
        title="雪落长安",
        chapter_number=1,
        scene_number=1,
        context="角色：沈青",
        scene_outline="场景 1：发现尸体",
        style="冷峻克制",
    )

    assert "场景规划" in plan_output
    assert "第 1 章" in plan_output
    assert "发现尸体" in plan_output
    assert "场景 1" in write_output
    assert "冷峻克制" in write_output
