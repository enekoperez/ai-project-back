import time

from google import genai
from google.genai import types
from loguru import logger

from webapp import config

MODEL = "gemini-3.1-flash-lite"
MAX_STEPS = 25
TEMPERATURE = 1.0

client = genai.Client(api_key=config.Config.GOOGLE_AI_API_KEY)


def generate(label, **kwargs):
    start = time.time()
    config_obj = kwargs.pop("config", None) or types.GenerateContentConfig()
    config_obj.temperature = TEMPERATURE
    response = client.models.generate_content(model=MODEL, config=config_obj, **kwargs)
    secs = round(time.time() - start, 2)
    logger.info(f"[llm {label}] {secs}s")
    return response, secs


# --- Sub-agents ---

def research_agent(task: str) -> str:
    response, _ = generate(
        "research",
        contents=f"""
You are a research specialist.

Provide factual explanations and gather information.
Do not write code.

Task:
{task}
""",
    )
    return response.text


def analysis_agent(task: str) -> str:
    response, _ = generate(
        "analysis",
        contents=f"""
You are an analyst.

Compare options, evaluate trade-offs, and structure findings with clear
pros and cons. Do not do raw research or write code.

Task:
{task}
""",
    )
    return response.text


def writing_agent(task: str) -> str:
    response, _ = generate(
        "writing",
        contents=f"""
You are a writer.

Compose clear, well-structured prose from the given material.
Do not write code.

Task:
{task}
""",
    )
    return response.text


def dev_agent(task: str) -> str:
    response, _ = generate(
        "dev",
        contents=f"""
You are a senior software engineer.

Write code and technical solutions.
Do not do general research.

Task:
{task}
""",
    )
    return response.text


def designer_agent(content: str) -> str:
    response, _ = generate(
        "designer",
        contents=f"""
You are a web designer with a warm, upbeat, friendly voice.

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


def delegate_to_analysis(query: str) -> str:
    return analysis_agent(query)


def delegate_to_writing(query: str) -> str:
    return writing_agent(query)


def delegate_to_dev(query: str) -> str:
    return dev_agent(query)


# --- Tool declarations ---

def _query_tool(name, description):
    return types.FunctionDeclaration(
        name=name,
        description=description,
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={"query": types.Schema(type=types.Type.STRING)},
            required=["query"],
        ),
    )


TOOLS = [
    types.Tool(
        function_declarations=[
            _query_tool("delegate_to_research", "Use for factual research questions and explanations"),
            _query_tool("delegate_to_analysis", "Use to compare options, weigh trade-offs, and analyze"),
            _query_tool("delegate_to_writing", "Use to compose clear prose or narrative text"),
            _query_tool("delegate_to_dev", "Use for programming and code tasks"),
        ]
    )
]

AGENT_BY_TOOL = {
    "delegate_to_research": "researcher",
    "delegate_to_analysis": "analyst",
    "delegate_to_writing": "writer",
    "delegate_to_dev": "developer",
}


# --- Tool dispatch ---

def execute_tool(name, args):
    if name == "delegate_to_research":
        return delegate_to_research(**args)
    if name == "delegate_to_analysis":
        return delegate_to_analysis(**args)
    if name == "delegate_to_writing":
        return delegate_to_writing(**args)
    if name == "delegate_to_dev":
        return delegate_to_dev(**args)
    raise ValueError(name)


# --- Orchestrator loop ---

def orchestrator(user_request: str) -> dict:
    start = time.time()
    contents: list[str | types.Content] = [user_request]
    agents_used: list[str] = []
    steps: list[dict] = []

    for i in range(1, MAX_STEPS + 1):
        response, _ = generate(
            f"orchestrator i:{i}",
            contents=contents,
            config=types.GenerateContentConfig(tools=TOOLS),
        )

        candidate = response.candidates[0]
        contents.append(candidate.content)

        tool_calls = [p.function_call for p in candidate.content.parts if getattr(p, "function_call", None)]
        if not tool_calls:
            logger.info(f"i:{i} no tool used -> designer")
            t = time.time()
            html = designer_agent(response.text)
            agents_used.append("designer")
            steps.append({"i": i, "finisher": "designer", "secs": round(time.time() - t, 2)})
            return {
                "answer_html": html,
                "agents_used": agents_used,
                "steps": steps,
                "total_secs": round(time.time() - start, 2),
            }

        for call in tool_calls:
            logger.info(f"i:{i} tool: {call.name}({dict(call.args)})")
            t = time.time()
            result = execute_tool(call.name, dict(call.args))
            agents_used.append(AGENT_BY_TOOL[call.name])
            steps.append({"i": i, "tool": call.name, "secs": round(time.time() - t, 2)})
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
        result = orchestrator(question)
        return result["answer_html"].replace("<pre>", _PRE_STYLE)
