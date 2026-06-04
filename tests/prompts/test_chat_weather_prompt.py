from webapp.prompts.chat_weather_prompt import build_system_prompt


def test_build_system_prompt_requires_weather_tool():
    prompt = build_system_prompt().lower()

    assert "always call `get_weather`" in prompt
    assert "do not answer from memory" in prompt
    assert "could not retrieve weather data" in prompt
