"""
AG2 Multi-Agent Orchestration with Atomic Agents Tools

This example demonstrates how AG2's GroupChat orchestration layer works together
with Atomic Agents' typed, schema-validated tools. AG2 handles multi-agent
conversation and coordination; Atomic Agents provides the typed tool layer with
Pydantic schema validation on every input and output.

Architecture:
    AG2 GroupChat (orchestration)
    ├── UserProxy      — sends the initial task, detects termination
    ├── ResearchAgent  — calls the WebSearchTool / CalculatorTool
    └── AnalystAgent   — synthesizes findings and emits TERMINATE

    Atomic Agents (typed tools)
    ├── WebSearchTool[SearchInput, SearchOutput]  — mock HTTP search
    └── CalculatorTool[CalcInput, CalcOutput]     — sympy evaluator

Bridge pattern: each Atomic Agents tool is wrapped in a plain function that is
registered with AG2 via @proxy.register_for_execution() /
@agent.register_for_llm(). The function constructs the typed input schema, calls
tool.run(), and returns model_dump_json() so AG2 agents receive structured text.
"""

import os
from dotenv import load_dotenv
from pydantic import Field
from sympy import sympify
import requests

from atomic_agents import BaseTool, BaseToolConfig, BaseIOSchema
from autogen import AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager, LLMConfig

load_dotenv()

# ---------------------------------------------------------------------------
# Atomic Agents — typed I/O schemas
# ---------------------------------------------------------------------------


class SearchInput(BaseIOSchema):
    """Input schema for the web search tool."""

    query: str = Field(..., description="Search query string")
    max_results: int = Field(default=5, description="Maximum number of results to return")


class SearchOutput(BaseIOSchema):
    """Output schema for the web search tool."""

    results: list[str] = Field(..., description="List of result snippets")
    sources: list[str] = Field(default_factory=list, description="Source URLs or identifiers")
    query_used: str = Field(..., description="The query that was executed")


class CalcInput(BaseIOSchema):
    """
    Input schema for the calculator tool. Supports arithmetic, algebra,
    exponentiation, and trigonometric expressions (e.g. 'sin(pi/2) + 2**3').
    """

    expression: str = Field(..., description="Mathematical expression to evaluate, e.g. '2 + 2' or 'sqrt(16)'")


class CalcOutput(BaseIOSchema):
    """Output schema for the calculator tool."""

    result: str = Field(..., description="Evaluated result as a string")
    expression_used: str = Field(..., description="The expression that was evaluated")


# ---------------------------------------------------------------------------
# Atomic Agents — tool configurations
# ---------------------------------------------------------------------------


class WebSearchConfig(BaseToolConfig):
    """Configuration for the WebSearchTool."""

    searxng_base_url: str = ""  # e.g. http://localhost:8080
    tavily_api_key: str = ""
    max_results: int = 5


class CalculatorConfig(BaseToolConfig):
    """Configuration for the CalculatorTool."""

    pass


# ---------------------------------------------------------------------------
# Atomic Agents — tool implementations
# ---------------------------------------------------------------------------


class WebSearchTool(BaseTool[SearchInput, SearchOutput]):
    """
    Web search tool with typed input/output schemas.

    Attempts, in order:
    1. Tavily API (if TAVILY_API_KEY is set)
    2. SearXNG instance (if SEARXNG_BASE_URL is set)
    3. Fallback: returns a clearly-labelled stub so the example runs
       end-to-end without any search credentials.
    """

    input_schema = SearchInput
    output_schema = SearchOutput

    def __init__(self, config: WebSearchConfig = WebSearchConfig()):
        super().__init__(config)

    def run(self, params: SearchInput) -> SearchOutput:
        config: WebSearchConfig = self.config  # type: ignore[assignment]

        # --- Tavily ---
        if config.tavily_api_key:
            try:
                resp = requests.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": config.tavily_api_key,
                        "query": params.query,
                        "max_results": params.max_results,
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
                results = [r.get("content", r.get("snippet", "")) for r in data.get("results", [])]
                sources = [r.get("url", "") for r in data.get("results", [])]
                return SearchOutput(results=results, sources=sources, query_used=params.query)
            except Exception as exc:
                return SearchOutput(
                    results=[f"Tavily search error: {exc}"],
                    sources=[],
                    query_used=params.query,
                )

        # --- SearXNG ---
        if config.searxng_base_url:
            try:
                resp = requests.get(
                    f"{config.searxng_base_url.rstrip('/')}/search",
                    params={
                        "q": params.query,
                        "format": "json",
                        "categories": "general",
                    },
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
                items = data.get("results", [])[: params.max_results]
                results = [r.get("content", r.get("title", "")) for r in items]
                sources = [r.get("url", "") for r in items]
                return SearchOutput(results=results, sources=sources, query_used=params.query)
            except Exception as exc:
                return SearchOutput(
                    results=[f"SearXNG search error: {exc}"],
                    sources=[],
                    query_used=params.query,
                )

        # --- Fallback stub (no credentials configured) ---
        stub_results = [
            f"[Stub] Result 1 for '{params.query}': AI agent frameworks like AG2 and Atomic Agents "
            "enable composable, schema-driven multi-agent pipelines.",
            f"[Stub] Result 2 for '{params.query}': AG2 provides GroupChat orchestration; "
            "Atomic Agents provides typed, Pydantic-validated tools.",
            f"[Stub] Result 3 for '{params.query}': The combination allows structured data flow "
            "between agents with runtime validation on every tool call.",
        ]
        return SearchOutput(
            results=stub_results[: params.max_results],
            sources=["https://docs.ag2.ai", "https://atomicagents.ai"],
            query_used=params.query,
        )


class CalculatorTool(BaseTool[CalcInput, CalcOutput]):
    """
    Calculator tool backed by sympy. Evaluates arithmetic and algebraic
    expressions with full type-safe input/output schemas.
    """

    input_schema = CalcInput
    output_schema = CalcOutput

    def __init__(self, config: CalculatorConfig = CalculatorConfig()):
        super().__init__(config)

    def run(self, params: CalcInput) -> CalcOutput:
        try:
            parsed = sympify(params.expression)
            result = str(parsed.evalf())
        except Exception as exc:
            result = f"Error evaluating expression: {exc}"
        return CalcOutput(result=result, expression_used=params.expression)


# ---------------------------------------------------------------------------
# Tool instantiation (reads env vars for optional credentials)
# ---------------------------------------------------------------------------

search_tool = WebSearchTool(
    config=WebSearchConfig(
        tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
        searxng_base_url=os.getenv("SEARXNG_BASE_URL", ""),
        max_results=5,
    )
)

calculator_tool = CalculatorTool()

# ---------------------------------------------------------------------------
# AG2 setup
# ---------------------------------------------------------------------------

llm_config = LLMConfig(
    {
        "model": "gpt-4o-mini",
        "api_key": os.getenv("OPENAI_API_KEY"),
        "api_type": "openai",
    }
)


def is_termination_msg(message: dict) -> bool:
    """Detect TERMINATE signal from analyst agent."""
    content = message.get("content", "") or ""
    return "TERMINATE" in content


user_proxy = UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config=False,
    is_termination_msg=is_termination_msg,
)

research_agent = AssistantAgent(
    name="research_agent",
    system_message=(
        "You are a research agent. Use the available tools to gather information.\n"
        "- Use search_web to look up topics and current information.\n"
        "- Use calculate to evaluate any numerical or mathematical expressions.\n"
        "Be thorough but concise. Pass your findings to the analyst agent."
    ),
    llm_config=llm_config,
)

analyst_agent = AssistantAgent(
    name="analyst_agent",
    system_message=(
        "You are an analyst agent. Synthesize research findings into a clear, "
        "well-structured answer. After providing your final answer, "
        "end your message with the word TERMINATE on its own line."
    ),
    llm_config=llm_config,
)

# ---------------------------------------------------------------------------
# Bridge: wrap Atomic Agents tools as AG2 registered functions
# Each function accepts plain Python types (AG2 handles schema generation),
# constructs the typed Atomic Agents input schema internally, and returns
# model_dump_json() so AG2 agents receive structured, readable output.
# ---------------------------------------------------------------------------


@user_proxy.register_for_execution()
@research_agent.register_for_llm(description="Search the web for information on a topic. Returns structured results.")
def search_web(query: str, max_results: int = 5) -> str:
    """AG2-registered wrapper around WebSearchTool."""
    output: SearchOutput = search_tool.run(SearchInput(query=query, max_results=max_results))
    return output.model_dump_json()


@user_proxy.register_for_execution()
@research_agent.register_for_llm(description="Evaluate a mathematical or algebraic expression using sympy.")
def calculate(expression: str) -> str:
    """AG2-registered wrapper around CalculatorTool."""
    output: CalcOutput = calculator_tool.run(CalcInput(expression=expression))
    return output.model_dump_json()


# ---------------------------------------------------------------------------
# GroupChat orchestration
# ---------------------------------------------------------------------------

group_chat = GroupChat(
    agents=[user_proxy, research_agent, analyst_agent],
    messages=[],
    max_round=12,
)

manager = GroupChatManager(
    groupchat=group_chat,
    llm_config=llm_config,
    is_termination_msg=is_termination_msg,
)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    task = (
        "Research and compare the top 3 AI agent frameworks in 2026. "
        "For each framework, describe its key design philosophy and primary use case. "
        "Also calculate how many months have passed since January 2024."
    )

    print("=" * 72)
    print("AG2 Multi-Agent Orchestration with Atomic Agents Tools")
    print("=" * 72)
    print(f"Task: {task}\n")

    result = user_proxy.run(manager, message=task)
    result.process()

    print("\n" + "=" * 72)
    print("Conversation complete.")
    if result.summary:
        print(f"\nSummary:\n{result.summary}")
    print("=" * 72)
