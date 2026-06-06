import os
import urllib.parse

import requests
from deepagents import create_deep_agent
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver

from webapp import config


class LangService:
    def __init__(self):
        os.environ["GOOGLE_API_KEY"] = config.Config.GOOGLE_AI_API_KEY

    @staticmethod
    def get_weather(city: str) -> str:
        """Get weather for a given city."""
        return f"It's always sunny in {city}!"

    def call_simple(self, request_json):
        question = request_json["question"]

        agent = create_agent(
            model=f"google_genai:{config.Config.DEFAULT_GOOGLE_AI_CHAT_API_MODEL}",
            tools=[self.get_weather],
            system_prompt="You are a helpful assistant",
        )

        result = agent.invoke(
            {"messages": [{"role": "user", "content": question}]}
        )
        response = result["messages"][-1].content_blocks
        return {"message": response}

    @staticmethod
    @tool
    def fetch_text_from_url(url: str) -> str:
        """Fetch the document from a URL.
        """
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            return "Fetch failed: URL must be an HTTP(S) URL with a host"

        try:
            resp = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; quickstart-research/1.0)"},
                timeout=120,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            return f"Fetch failed: {e}"
        return resp.content.decode("utf-8", errors="replace")

    def call_complex(self):
        SYSTEM_PROMPT = """You are a literary data assistant.
        ## Capabilities
        - `fetch_text_from_url`: loads document text from a URL into the conversation.
        Do not guess line counts or positions—ground them in tool results from the saved file."""

        model = init_chat_model(
            config.Config.DEFAULT_GOOGLE_AI_CHAT_API_MODEL,  # model="gemini-3.1-pro-preview",
            model_provider="google-genai",
            temperature=0.5,
            timeout=600,
            max_tokens=25000,
            streaming=True,
        )

        checkpointer = InMemorySaver()

        agent = create_agent(
            model=model,
            tools=[self.fetch_text_from_url],
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
        )

        deep_agent = create_deep_agent(
            model=model,
            tools=[self.fetch_text_from_url],
            system_prompt=SYSTEM_PROMPT,
            checkpointer=checkpointer,
        )

        content = """Project Gutenberg hosts a full plain-text copy of F. Scott Fitzgerald's The Great Gatsby.
        URL: https://www.gutenberg.org/files/64317/64317-0.txt

        Answer as much as you can:

        1) How many lines in the complete Gutenberg file contain the substring `Gatsby` (count lines, not occurrences within a line, each line ends with a line break).
        2) The 1-based line number of the first line in the file that contains `Daisy`.
        3) A two-sentence neutral synopsis.

        Do your best on (1) and (2). If at any point you realize you cannot **verify** an exact answer with
        your available tools and reasoning, do not fabricate numbers: use `null` for that field and spell out
        the limitation in `how_you_computed_counts`. If you encounter any errors please report what the error was and what the error message was."""

        agent_result = agent.invoke(
            {"messages": [{"role": "user", "content": content}]},
            config={"configurable": {"thread_id": "great-gatsby-lc"}},
        )
        deep_agent_result = deep_agent.invoke(
            {"messages": [{"role": "user", "content": content}]},
            config={"configurable": {"thread_id": "great-gatsby-da"}},
        )
        agent_response = agent_result["messages"][-1].content_blocks
        deep_agent_response = deep_agent_result["messages"][-1].content_blocks

        return {"agent_response": agent_response, "deep_agent_response": deep_agent_response}
