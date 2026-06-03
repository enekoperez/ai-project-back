from google.genai import types


class ChatTools:
    def __init__(self):
        # self.headers = dict(request_headers)
        # self.user_id = user_id
        pass

    def declarations(self):
        return [
            types.FunctionDeclaration(
                name="get_weather",
                description=(
                    "Get the weather for a city. This is a mock tool: cities starting with a vowel return "
                    "good weather; other cities return bad weather."
                ),
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "city": types.Schema(
                            type=types.Type.STRING,
                            description="City to get the weather for.",
                        ),
                    },
                    required=["city"],
                ),
            ),
        ]

    def dispatch(self):
        return {
            "get_weather": self._get_weather,
        }

    def _get_weather(self, city: str) -> dict:
        print(f">>> TOOL CALLED: get_weather city={city}")
        condition = "good" if city.strip().lower().startswith(("a", "e", "i", "o", "u")) else "bad"
        return {
            "city": city,
            "forecast": f"The weather in {city} is {condition}.",
            "condition": condition,
        }
