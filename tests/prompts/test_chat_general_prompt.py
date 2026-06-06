from webapp.prompts.chat_general_prompt import build_system_prompt, build_user_prompt


def test_build_system_prompt_instructs_rag_context_only_answers():
    prompt = build_system_prompt().lower()

    assert "answer using only the help context" in prompt
    assert "i don't know from the available help docs" in prompt
    assert "same language" in prompt
    assert "todo:" not in prompt


def test_build_user_prompt_includes_chunks_and_question():
    prompt = build_user_prompt(
        chunks=[
            {
                "source_name": "football.md",
                "score": 0.87654,
                "text": "Football teams have eleven players.",
            }
        ],
        question="How many players are on a football team?",
    )

    assert "<help_context>" in prompt
    assert '<chunk source_name="football.md" score="0.8765">' in prompt
    assert "Football teams have eleven players." in prompt
    assert "Question: How many players are on a football team?" in prompt
