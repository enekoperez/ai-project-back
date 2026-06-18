from webapp.prompts.rerank_prompt import build_system_prompt, build_user_prompt, response_format


def test_build_system_prompt_describes_reranker_role():
    prompt = build_system_prompt().lower()

    assert "reranker" in prompt
    assert "most to least relevant" in prompt
    assert "drop unrelated" in prompt
    assert '{"indices": [<int>, ...]}' in prompt
    assert "todo:" not in prompt


def test_build_user_prompt_numbers_candidates_and_includes_query():
    prompt = build_user_prompt(
        query="How many players are on a football team?",
        chunks=[
            {"text": "Football teams have eleven players."},
            {"text": "Basketball teams have five players."},
        ],
    )

    assert "<candidates>" in prompt
    assert "</candidates>" in prompt
    assert "[0] Football teams have eleven players." in prompt
    assert "[1] Basketball teams have five players." in prompt
    assert "Query: How many players are on a football team?" in prompt


def test_response_format_declares_indices_integer_array():
    schema = response_format()

    assert schema["type"] == "object"
    assert schema["properties"]["indices"]["type"] == "array"
    assert schema["properties"]["indices"]["items"] == {"type": "integer"}
    assert schema["required"] == ["indices"]
