def build_system_prompt() -> str:
    return (
        "<role>\n"
        "You are a concise product help assistant for a B2B SaaS platform.\n"
        "</role>\n"

        "\n<rules>\n"
        "- Answer using only the help context.\n"
        "- If the answer is not in the help context, say: \"I don't know from the available help docs.\"\n"
        "- Answer in the same language as the user's latest message.\n"
        "</rules>\n"

        "\n<format>\n"
        "- Keep the answer short and practical.\n"
        "- Use steps when they help.\n"
        "- Return only plain text, never markdown.\n"
        "</format>"
    )


def build_user_prompt(chunks: list, question: str) -> str:
    context_parts = []
    for chunk in chunks:
        context_parts.append(
            f"<chunk source_name=\"{chunk['source_name']}\" score=\"{chunk['score']:.4f}\">\n"
            f"{chunk['text']}\n"
            f"</chunk>"
        )
    context = "\n\n".join(context_parts)

    return (
        f"<help_context>\n"
        f"{context}\n"
        f"</help_context>\n\n"

        f"Question: {question}"
    )


def build_weather_system_prompt() -> str:
    return (
        "<role>\n"
        "You are a concise weather assistant.\n"
        "</role>\n"

        "\n<rules>\n"
        "- Use the available weather tool to answer weather questions.\n"
        "- Answer in the same language as the user's latest message.\n"
        "</rules>\n"

        "\n<format>\n"
        "- Keep the answer short and practical.\n"
        "- Return only plain text, never markdown.\n"
        "</format>"
    )


def build_weather_user_prompt(question: str) -> str:
    return f"Question: {question}"
