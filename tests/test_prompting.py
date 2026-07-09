from novel_agent.prompting import render_prompt


def test_render_prompt_uses_packaged_template():
    output = render_prompt("chapter_write.j2", title="试写", chapter_number=1, chapter_goal="主角发现线索", context="暂无", style="克制、悬疑")

    assert "试写" in output
    assert "第 1 章" in output
    assert "主角发现线索" in output
