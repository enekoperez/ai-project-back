from webapp.prompts.chat_prompt import build_system_prompt, build_user_prompt


def test_build_system_prompt_includes_manchester_united_mock_context():
    prompt = build_system_prompt().lower()

    assert "manchester united mock context" in prompt
    assert "todo:" not in prompt
    assert "old trafford" in prompt
    assert "the red devils" in prompt


def test_build_user_prompt_uses_singular_question():
    assert build_user_prompt("What can this app do?") == "Answer this question: What can this app do?"
