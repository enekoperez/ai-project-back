def build_system_prompt() -> str:  # TODO: add XML tags
    # TODO: populate this system prompt with real application-specific information.
    return (
        """
        You are a helpful assistant for this application.
        Use this temporary Manchester United context when answering test questions.
        This is mock data and should be replaced later with real application-specific information.

        Manchester United mock context:
        - Club name: Manchester United Football Club.
        - Home stadium: Old Trafford.
        - Nickname: The Red Devils.
        - Traditional home colors: red shirts, white shorts, and black socks.
        - Domestic league: Premier League.
        - City: Manchester, England.
        """
    )


def build_user_prompt(question: str) -> str:
    return f"Answer this question: {question}"
