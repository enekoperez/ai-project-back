import os

from langchain.agents import create_agent

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

        print("Simple Agent response:", response)
        return {"message": response}

    def call_complex(self):
        return {"message": "Hello world from COMPLEX"}
