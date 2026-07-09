from novel_agent.models import ChapterPlan, Character, NovelConfig


def test_novel_config_has_sensible_defaults():
    config = NovelConfig(title="天外来客")

    assert config.title == "天外来客"
    assert config.language == "zh-CN"
    assert config.genre == "未设定"
    assert config.target_words == 100_000


def test_chapter_plan_default_status_is_planned():
    chapter = ChapterPlan(number=1, title="开端", goal="主角登场")

    assert chapter.status == "planned"
    assert chapter.conflict == ""


def test_character_keeps_voice_and_secrets():
    character = Character(name="沈青", role="主角", goals=["寻找记忆"], secrets=["曾是反派首领"], voice="冷静克制")

    assert character.name == "沈青"
    assert "寻找记忆" in character.goals
    assert "曾是反派首领" in character.secrets
    assert character.voice == "冷静克制"
