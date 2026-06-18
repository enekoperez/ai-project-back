def build_system_prompt() -> str:
    return (
        "<role>\n"
        "You are a passage reranker for a retrieval system.\n"
        "</role>\n"

        "\n<rules>\n"
        "- Given a query and numbered candidate passages, judge how well each passage answers the query.\n"
        "- Return all candidate indices ordered from most to least relevant; do not omit any.\n"
        "</rules>\n"

        "\n<format>\n"
        "- Respond with JSON: {\"indices\": [<int>, ...]} using the candidate numbers shown in brackets.\n"
        "</format>"
    )


def build_user_prompt(query: str, chunks: list) -> str:
    candidates = "\n\n".join(f"[{index}] {chunk['text']}" for index, chunk in enumerate(chunks))

    return (
        f"<candidates>\n"
        f"{candidates}\n"
        f"</candidates>\n\n"

        f"Query: {query}"
    )


def response_format() -> dict:
    return {
        "type": "object",
        "properties": {
            "indices": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Candidate indices, most relevant first.",
            },
        },
        "required": ["indices"],
    }
