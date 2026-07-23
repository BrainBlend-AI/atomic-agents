---
name: create-atomic-tool
description: Build a `BaseTool[InSchema, OutSchema]` subclass — input/output schemas, `BaseToolConfig`, `run()` (and optional `run_async()`), env-driven secrets, typed failure outputs. Use when the user asks to "add a tool", "create a tool", "wrap an API as a tool", "build a `BaseTool`", "make a calculator/search/weather tool", or runs `/atomic-agents:create-atomic-tool`.
---

# Create an Atomic Agents Tool

A tool is a deterministic capability an agent can invoke. In Atomic Agents, every tool is a `BaseTool[InSchema, OutSchema]` subclass with a typed `run()` (and optional `run_async()`). The input/output schemas double as the tool's signature for the LLM and as Pydantic validation at runtime.

For deep material (MCP interop, distributing as a standalone package, advanced error patterns), the authority is `../framework/references/tools.md`. This skill is the action-oriented path: clarify → write → verify.

## When this fires vs the umbrella `framework` skill

- **This skill**: the user is creating a specific tool — wrapping an API, building a calculator, scraping a page, querying a DB.
- **`framework` skill**: questions about Atomic Agents in general, or the user is doing something other than authoring a tool.
- **`find-forge-tools` skill**: the user needs a capability and should check configured Forge sources for an existing tool first.

## Phase 1 — Clarify

Bundle into one message:

1. **What does the tool do?** One sentence. This becomes the class docstring and feeds the LLM's tool description.
2. **Inputs and outputs.** Names, types, units. If unclear, propose a schema pair and confirm.
3. **External dependencies.** HTTP API? DB? Local computation only? If HTTP, what auth (API key env var, OAuth, none)?
4. **Sync, async, or both?** If the rest of the project is async or the call is I/O bound, plan a `run_async()` alongside `run()`.
5. **Failure modes.** Rate limits, not-found, network errors — how should the agent see them? Default: typed failure output, not raised exceptions.

Skip any question already answered in context.

## Phase 2 — Plan

Confirm the location and shape in one short block, then proceed:

- File: `<project>/tools/<tool_name>_tool.py` (in-project tool — see `../framework/references/project-structure.md`).
- Schemas: `<ToolName>Input`, `<ToolName>Output`, optionally a typed failure shape.
- Config: `<ToolName>Config(BaseToolConfig)` if the tool needs API keys, base URLs, timeouts, retries.
- Sync vs async: pick one or both.
- Error pattern: typed failure output (preferred) vs raise (only for programmer error).

## Phase 3 — Implement

### Skeleton — local computation, no config

```python
from pydantic import Field
from atomic_agents import BaseIOSchema, BaseTool


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
```

### Skeleton — HTTP-backed, with config and typed failure

```python
import os
import httpx
from typing import Literal, Optional
from pydantic import Field
from atomic_agents import BaseIOSchema, BaseTool, BaseToolConfig


class WeatherConfig(BaseToolConfig):
    api_key: str = Field(
        default_factory=lambda: os.environ.get("WEATHER_API_KEY", ""),
        description="API key for the weather service.",
    )
    base_url: str = Field(
        default="https://api.weather.example/v1",
        description="Base URL for the weather API.",
    )
    timeout: float = Field(default=15.0, ge=1.0, le=120.0, description="Request timeout (s).")


class WeatherInput(BaseIOSchema):
    """A request for current weather conditions."""
    city: str = Field(..., description="City name, e.g. 'Brussels'.")


class WeatherOutput(BaseIOSchema):
    """Current weather conditions, or a typed failure."""
    status: Literal["ok", "error"] = Field(..., description="Outcome code.")
    temperature_c: Optional[float] = Field(default=None, description="Temperature in Celsius.")
    summary: Optional[str] = Field(default=None, description="Human-readable summary.")
    error: Optional[str] = Field(default=None, description="Failure message when status='error'.")


class WeatherTool(BaseTool[WeatherInput, WeatherOutput]):
    """Fetch current conditions for a city from the weather API."""

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

    async def run_async(self, params: WeatherInput) -> WeatherOutput:
        cfg: WeatherConfig = self.config
        if not cfg.api_key:
            return WeatherOutput(status="error", error="WEATHER_API_KEY not set")
        async with httpx.AsyncClient(timeout=cfg.timeout) as client:
            try:
                r = await client.get(
                    f"{cfg.base_url}/current",
                    params={"city": params.city},
                    headers={"Authorization": f"Bearer {cfg.api_key}"},
                )
                r.raise_for_status()
            except httpx.HTTPError as e:
                return WeatherOutput(status="error", error=str(e))
        data = r.json()
        return WeatherOutput(status="ok", temperature_c=data["temp_c"], summary=data["summary"])
```

### Hard rules

- Generic parameters carry the runtime type info. **Never** also assign `input_schema` / `output_schema` as class attributes — it shadows the framework-managed property.
- `run()` returns the **output schema instance**, not a dict.
- Secrets via env / `BaseToolConfig`, never hardcoded.
- HTTP tools always set a timeout. Tools run in the agent's request path.
- The async hook is `async def run_async`, not `arun` — the framework calls `run_async`.
- Convert routine failures (rate limits, 404s, validation rejects from the upstream API) into a typed failure output. Reserve `raise` for programmer error.

## Phase 4 — Package it for the forge

When the user wants a reusable or downloadable tool, emit a complete forge package instead of loose project files. Before creating a new tool, check `../find-forge-tools/SKILL.md` when that skill is available, then inspect the forge index and existing tools so the name and capability are not duplicated.

Create this directory tree, file for file:

```text
tool_name/
│   .coveragerc
│   pyproject.toml
│   README.md
│   requirements.txt
│   uv.lock
│
├── tool/
│   │   tool_name.py
│   │   some_util_file.py
│   │   another_util_file.py
│
└── tests/
    │   test_tool_name.py
    │   test_some_util_file.py
    │   test_another_util_file.py
```

The package must include:

- `.coveragerc`, copied from the standard forge configuration.
- `pyproject.toml`, with the tool name, version, description, `README.md` readme, Python requirement, runtime dependencies, and the standard development dependency group. Keep runtime dependencies under `[project].dependencies` and development-only dependencies under `[dependency-groups].dev`.
- `requirements.txt`, containing exactly the runtime dependencies from `pyproject.toml`, with the Python version constraint omitted. Do not copy development dependencies into this file.
- `tool/`, containing the implementation and any small helper modules. Keep the public tool class, input/output schemas, and config in importable modules.
- `tests/`, containing tests for the schemas, configuration, success path, and routine failure paths. Add focused tests for HTTP or async behavior when those paths exist.
- `README.md`, with these standard sections: Overview, Prerequisites and Dependencies, Installation, Configuration when the tool needs it, Input & Output Structure, Usage, Contributing, and License.
- `uv.lock`, generated by running `uv sync` from the package directory after metadata and dependencies are complete.

Run `uv sync` before handing off the package. The generated package must be self-contained and importable from its own directory, while still following the `BaseIOSchema`, `BaseToolConfig`, and explicit `BaseTool[Input, Output]` contracts above.

## Phase 5 — Wire it into an agent

Two integration shapes (see `../framework/references/tools.md` for more):

**Single-tool agent** — agent's output schema **is** the tool's input schema:

```python
agent = AtomicAgent[UserQuery, WeatherInput](config=config)
tool = WeatherTool()

call = agent.run(UserQuery(question="weather in Brussels?"))
result = tool.run(call)
```

**Router agent** — agent picks among tools via a discriminated union of tool-call schemas. Use this when the agent has 2–10 tools to choose from. For dozens, see the search+execute pattern in `../framework/references/orchestration.md`.

## Phase 6 — Verify

For a forge package, run the package smoke test and the forge conformance suite from the repository root:

```bash
uv run python -c "from <project>.tools.<tool_name>_tool import <ToolName>Tool, <ToolName>Input; t = <ToolName>Tool(); print(t.run(<ToolName>Input(...)))"
uv run pytest atomic-forge/conformance
```

The conformance suite must pass against the generated package before handoff. It checks the required forge layout, clean imports, schema and config contracts, explicit `BaseTool` generics, runtime dependency parity, and index metadata. If imports fail with the docstring error, add the docstring on the schema. If `self.input_schema` is `None`, the generic parameters are missing — write `class FooTool(BaseTool[FooInput, FooOutput]):`, not `class FooTool(BaseTool)`.

## Phase 7 — Hand off

Tell the user:

- Where the tool lives and what to import.
- How the agent should use it (single-tool or router shape).
- Optional next steps:
  - The agent that calls it → `create-atomic-agent` skill.
  - Multi-agent wiring around the tool → `../framework/references/orchestration.md`.
  - MCP interop or packaging the tool for distribution → `../framework/references/tools.md`.

## Anti-patterns

- `class FooTool(BaseTool):` with `input_schema = ...` class attributes — use generics: `BaseTool[FooInput, FooOutput]`.
- Returning a dict or primitive from `run()` instead of `OutputSchema(...)`.
- Raising on routine upstream failures — model them as typed output.
- No timeout on HTTP / DB calls.
- `MCPTransportType.STREAMABLE_HTTP` — the correct value is `HTTP_STREAM`.
- Implementing `async def arun(...)` — the framework calls `run_async`.

For deeper material — MCP interop, packaging a tool for `atomic download`, advanced router patterns — load `../framework/references/tools.md`.
