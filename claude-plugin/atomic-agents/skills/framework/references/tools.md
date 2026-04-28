# Tools (`BaseTool`)

## Contents
- The generic pattern
- Config, auth, and env vars
- `run()` and `run_async()` contract
- Error handling
- Integrating tools with agents
- MCP interop
- Prebuilt tools from Atomic Forge
- Distributing a standalone tool
- Common mistakes

## The generic pattern

`BaseTool` uses PEP 695 generics. The input and output schemas are declared as type parameters; the framework reads them back at class-creation time and exposes them as `self.input_schema` / `self.output_schema`.

```python
from pydantic import Field
from atomic_agents import BaseIOSchema, BaseTool, BaseToolConfig


class CalculatorInput(BaseIOSchema):
    """Arithmetic expression to evaluate."""
    expression: str = Field(..., description="Python-style arithmetic, e.g. '2 + 2 * 3'.")


class CalculatorOutput(BaseIOSchema):
    """Result of evaluating the expression."""
    result: float = Field(..., description="Numeric result.")


class CalculatorTool(BaseTool[CalculatorInput, CalculatorOutput]):
    """Evaluate simple arithmetic expressions safely."""

    def run(self, params: CalculatorInput) -> CalculatorOutput:
        import ast, operator as op
        ops = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv}
        def ev(n):
            if isinstance(n, ast.Constant): return n.value
            if isinstance(n, ast.BinOp): return ops[type(n.op)](ev(n.left), ev(n.right))
            raise ValueError("unsupported")
        return CalculatorOutput(result=ev(ast.parse(params.expression, mode="eval").body))


tool = CalculatorTool()
```

Do not assign `input_schema` / `output_schema` as class attributes. The generic parameters carry the type information via `BaseTool.__init_subclass__`, and the base class exposes both as properties. Declaring them as class attributes in addition is redundant at best and masks the framework-managed property at worst.

`self.tool_name` and `self.tool_description` default to the input schema's `title` and docstring. Override them with `BaseToolConfig(title=..., description=...)` when a different surface is needed for the LLM.

Canonical real tools to read: `atomic-forge/tools/calculator/tool/calculator.py` (minimal) and `atomic-forge/tools/searxng_search/tool/searxng_search.py` (HTTP-backed, with `run_async`).

## Config, auth, and env vars

`BaseToolConfig` carries `title` and `description` overrides. Subclass it for tool-specific configuration:

```python
import os
from pydantic import Field
from atomic_agents import BaseToolConfig

class WeatherConfig(BaseToolConfig):
    api_key: str = Field(
        default_factory=lambda: os.environ.get("WEATHER_API_KEY", ""),
        description="API key for the weather service.",
    )
    base_url: str = Field(
        default="https://api.weather.example/v1",
        description="Base URL for the weather API.",
    )
    timeout: float = Field(default=15.0, ge=1.0, le=120.0, description="Request timeout in seconds.")
```

Secrets come from environment. Never hardcode keys. Timeouts and retries belong in the config too.

## `run()` and `run_async()` contract

- Signature: `def run(self, params: InputSchema) -> OutputSchema`.
- `run()` is abstract on `BaseTool`; subclasses must implement it.
- For async-first tools, add `async def run_async(self, params: InputSchema) -> OutputSchema`. Callers that already have an event loop should prefer it. See `atomic-forge/tools/searxng_search/tool/searxng_search.py` for the dual-interface pattern.
- Return an `OutputSchema` instance, never raw dicts.
- Validate external side effects (HTTP status, DB result) and convert failures into either a successful output schema or a typed failure output (see `schemas.md` → error-schema pattern).

## Error handling

Two patterns, choose per call site:

1. **Typed failure output** — include a success/failure union in `OutputSchema`. The agent branches on it. Preferred when another agent invokes the tool.

2. **Exceptions** — only for programmer errors (misuse), not user-facing failures. Callers will not catch them routinely.

For external API calls:

```python
import httpx
from atomic_agents import BaseTool

class WeatherTool(BaseTool[WeatherInput, WeatherOutput]):
    """Fetch current conditions for a city."""

    def __init__(self, config: WeatherConfig | None = None):
        super().__init__(config or WeatherConfig())

    def run(self, params: WeatherInput) -> WeatherOutput:
        cfg: WeatherConfig = self.config
        if not cfg.api_key:
            return WeatherOutput(status="error", error="WEATHER_API_KEY not set")
        try:
            r = httpx.get(
                f"{cfg.base_url}/current",
                params={"city": params.city},
                headers={"Authorization": f"Bearer {cfg.api_key}"},
                timeout=cfg.timeout,
            )
            r.raise_for_status()
        except httpx.HTTPError as e:
            return WeatherOutput(status="error", error=str(e))
        data = r.json()
        return WeatherOutput(status="ok", temperature_c=data["temp_c"], summary=data["summary"])
```

## Integrating tools with agents

Tools plug into agents through the agent's output schema. Two common shapes:

**Single-tool agent.** The agent's output schema is the tool input schema. The agent decides arguments, the caller runs the tool:

```python
agent = AtomicAgent[UserQuery, CalculatorInput](config=config)
tool = CalculatorTool()

query = UserQuery(question="What's 23 times 47?")
call = agent.run(query)              # LLM picks the arguments
result = tool.run(call)              # host runs the tool
```

**Router agent.** The agent picks among tools by returning a discriminated union:

```python
from typing import Literal, Union

class CalcCall(BaseIOSchema):
    """Invoke the calculator."""
    tool: Literal["calculator"] = "calculator"
    args: CalculatorInput

class SearchCall(BaseIOSchema):
    """Invoke web search."""
    tool: Literal["search"] = "search"
    args: SearchInput

class ToolChoice(BaseIOSchema):
    """One of the available tools with its arguments."""
    call: Union[CalcCall, SearchCall] = Field(..., description="Tool invocation.")

agent = AtomicAgent[UserQuery, ToolChoice](config=config)
```

Working example: `atomic-examples/orchestration-agent/` orchestrates calculator + SearXNG with typed routing.

For larger tool surfaces (dozens+), see `orchestration.md` for the search+execute pattern.

## MCP interop

`atomic_agents.connectors.mcp` turns an MCP server's tools into `BaseTool` subclasses:

```python
from atomic_agents.connectors.mcp import fetch_mcp_tools, MCPTransportType

tools = fetch_mcp_tools(
    transport=MCPTransportType.HTTP_STREAM,      # also: SSE, STDIO
    endpoint="https://my-mcp-server.example/mcp",
)
# tools is a list[type[BaseTool]] — instantiate and use them like any other tool.
```

Async variants (`fetch_mcp_tools_async`, `fetch_mcp_resources_async`, `fetch_mcp_prompts_async`) and the lower-level `MCPFactory` are exported from the same module. Transport values are `SSE`, `HTTP_STREAM`, `STDIO` — not `STREAMABLE_HTTP`.

Full client-side example: `atomic-examples/mcp-agent/example-client/`. A matching server lives under `atomic-examples/mcp-agent/example-mcp-server/`.

## Prebuilt tools (Atomic Forge)

The `atomic-forge` workspace ships production-ready tools: calculator, SearXNG, Tavily, Bocha, YouTube transcript scraper, webpage scraper, and more. Install into a project with:

```bash
atomic download calculator
atomic download tavily_search
```

Treat them as reference implementations when writing new tools.

## Distributing a standalone tool

In-project tools live alongside agents (`<project>/tools/<name>_tool.py`) — see `project-structure.md`. A tool meant to be **distributed** (installable via `atomic download` or as its own package) uses a different layout: its own `pyproject.toml`, `tests/`, `requirements.txt`, `README.md`, and a `tool/` subdirectory for the implementation. Follow `atomic-forge/guides/tool_structure.md` when packaging for distribution.

## Common mistakes

- Declaring `input_schema = ...` / `output_schema = ...` as class attributes — use generics.
- Returning dicts or primitives from `run()` instead of the output schema.
- Raising on routine failures (rate limits, not-found) — model them as typed output instead.
- Forgetting a timeout on HTTP / database calls — tools invoked by an agent run synchronously in the request path.
- Implementing `async def arun(...)` — the framework calls `run_async`, not `arun`.
- Using `MCPTransportType.STREAMABLE_HTTP` — the correct value is `HTTP_STREAM`.
