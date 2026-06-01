def build_system_prompt() -> str:
    return (
        """
        You answer questions about the provided file. Be concise and only use the file content.
        """
    )


def build_user_prompt(questions: list) -> str:
    return f"Answer the following questions about the file: {questions}"
