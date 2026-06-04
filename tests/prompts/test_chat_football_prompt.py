from webapp.prompts.chat_football_prompt import build_system_prompt


def test_build_system_prompt_describes_football_assistant_without_tools():
    prompt = build_system_prompt(football_data="League table data").lower()

    assert "football assistant" in prompt
    assert "do not use external tools" in prompt
    assert "same language" in prompt
    assert "<context>" in prompt
    assert "league table data" in prompt
    assert "todo:" not in prompt
