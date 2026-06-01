from webapp.prompts.ocr_prompt import build_system_prompt, build_user_prompt


def test_build_system_prompt_describes_ocr_task():
    assert "answer questions about the provided file" in build_system_prompt().lower()


def test_build_user_prompt_lists_questions():
    assert build_user_prompt(["First?", "Second?"]) == (
        "Answer the following questions about the file: ['First?', 'Second?']"
    )
