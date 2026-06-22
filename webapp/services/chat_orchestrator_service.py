import time

from google import genai
from google.genai import types

from webapp import config

MODEL = "gemini-3.1-flash-lite"
MAX_STEPS = 8
TEMPERATURE = 1.0

client = genai.Client(api_key=config.Config.GOOGLE_AI_API_KEY)


def generate(label, **kwargs):
    start = time.time()
    config_obj = kwargs.pop("config", None) or types.GenerateContentConfig()
    config_obj.temperature = TEMPERATURE
    response = client.models.generate_content(model=MODEL, config=config_obj, **kwargs)
    print(f"[llm {label}] {time.time() - start:.2f}s")
    return response


# --- Sub-agents ---

def research_agent(task: str) -> str:
    response = generate(
        "research",
        contents=f"""
You are a research specialist.

Provide factual explanations.
Do not write code.

Task:
{task}
""",
    )
    return response.text


def coding_agent(task: str) -> str:
    response = generate(
        "coding",
        contents=f"""
You are a senior Python engineer.

Write code and technical solutions.
Do not do general research.

Task:
{task}
""",
    )
    return response.text


def writer_agent(content: str) -> str:
    response = generate(
        "writer",
        contents=f"""
You are an HTML writer with a warm, upbeat, friendly voice.

Turn all the information below into one clean, well-structured HTML fragment.
Use <h2>/<h3> headings, <p> paragraphs, and <ul>/<li> lists where it helps.
Make it feel happy and inviting: a friendly tone, and a relevant emoji at the
start of each heading and list item (don't overdo it).
Wrap any code EXACTLY as-is in <pre><code>...</code></pre> — do not change the code.
Return only the HTML fragment. No markdown, no ```html fences, no <html>/<body> wrapper.

Content:
{content}
""",
    )
    return response.text


# --- Delegation wrappers ---

def delegate_to_research(query: str) -> str:
    return research_agent(query)


def delegate_to_coding(query: str) -> str:
    return coding_agent(query)


# --- Tool declarations ---

research_tool = types.FunctionDeclaration(
    name="delegate_to_research",
    description="Use for research questions and explanations",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={"query": types.Schema(type=types.Type.STRING)},
        required=["query"],
    ),
)

coding_tool = types.FunctionDeclaration(
    name="delegate_to_coding",
    description="Use for programming and code tasks",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={"query": types.Schema(type=types.Type.STRING)},
        required=["query"],
    ),
)

TOOLS = [types.Tool(function_declarations=[research_tool, coding_tool])]


# --- Tool dispatch ---

def execute_tool(name, args):
    if name == "delegate_to_research":
        return delegate_to_research(**args)
    if name == "delegate_to_coding":
        return delegate_to_coding(**args)
    raise ValueError(name)


# --- Orchestrator loop ---

def orchestrator(user_request: str) -> str:
    contents: list[str | types.Content] = [user_request]

    for i in range(1, MAX_STEPS + 1):
        response = generate(
            f"orchestrator i:{i}",
            contents=contents,
            config=types.GenerateContentConfig(tools=TOOLS),
        )

        candidate = response.candidates[0]
        contents.append(candidate.content)

        tool_calls = [p.function_call for p in candidate.content.parts if getattr(p, "function_call", None)]
        if not tool_calls:
            print(f"i:{i} no tool used -> writer")
            return writer_agent(response.text)

        for call in tool_calls:
            print(f"i:{i} tool: {call.name}({dict(call.args)})")
            result = execute_tool(call.name, dict(call.args))
            contents.append(
                types.Content(
                    role="tool",
                    parts=[types.Part.from_function_response(name=call.name, response={"result": result})],
                )
            )

    raise RuntimeError("Step limit exceeded")


_PRE_STYLE = (
    '<pre style="background:#1e1e1e;color:#e6e6e6;padding:14px;'
    'border-radius:8px;overflow:auto;font-size:14px;line-height:1.5;">'
)


class ChatOrchestratorService:
    def chat(self, request_json):
        question = request_json["question"]
        html = orchestrator(question)
        return html.replace("<pre>", _PRE_STYLE)
