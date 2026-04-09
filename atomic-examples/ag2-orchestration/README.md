# AG2 Multi-Agent Orchestration with Atomic Agents

This example demonstrates framework composition: **AG2** handles multi-agent
conversation orchestration while **Atomic Agents** provides typed,
schema-validated tools. The two frameworks serve complementary roles — AG2
coordinates *what* agents do; Atomic Agents ensures *how* they do it is type-safe
and validated at runtime via Pydantic.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    AG2 Orchestration Layer                    │
│                                                              │
│  ┌────────────┐   task    ┌────────────────┐   findings      │
│  │ UserProxy  │ ────────► │ ResearchAgent  │ ──────────────► │
│  │            │           │ (calls tools)  │                 │
│  │ detects    │           └────────┬───────┘    ┌──────────┐ │
│  │ TERMINATE  │◄──────────────────┼────────────│ Analyst  │ │
│  └────────────┘    TERMINATE      │            │ Agent    │ │
│                                   │            └──────────┘ │
└───────────────────────────────────┼─────────────────────────┘
                                    │ bridge (typed wrappers)
┌───────────────────────────────────▼─────────────────────────┐
│                  Atomic Agents Tool Layer                     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ WebSearchTool[SearchInput, SearchOutput]            │    │
│  │  • Pydantic validation on every call                │    │
│  │  • Tavily / SearXNG / stub fallback                 │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ CalculatorTool[CalcInput, CalcOutput]               │    │
│  │  • sympy expression evaluator                       │    │
│  │  • Pydantic validation on every call                │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### Conversation flow

1. `UserProxy` sends the task to the GroupChat.
2. `ResearchAgent` receives the task and calls `search_web` and/or `calculate`
   (both are Atomic Agents tools wrapped as AG2 registered functions).
3. Each tool call validates its input schema (Pydantic), executes, validates its
   output schema, then returns `model_dump_json()` back to the AG2 agent.
4. `AnalystAgent` synthesizes the research into a final answer and ends the
   conversation with `TERMINATE`.
5. `UserProxy`'s `is_termination_msg` callback detects `TERMINATE` and cleanly
   stops the GroupChat.

### Bridge pattern

Atomic Agents tools are wrapped as AG2 registered functions:

```python
@user_proxy.register_for_execution()
@research_agent.register_for_llm(description="Search the web for information")
def search_web(query: str, max_results: int = 5) -> str:
    # Constructs typed Atomic Agents schema internally
    output: SearchOutput = search_tool.run(SearchInput(query=query, max_results=max_results))
    # Returns structured JSON string for AG2 agents to reason over
    return output.model_dump_json()
```

This keeps the two frameworks cleanly separated:
- **AG2** never needs to know about Pydantic schemas or Instructor.
- **Atomic Agents** tools never need to know about AG2's messaging protocol.

## Prerequisites

- Python ≥ 3.12
- `OPENAI_API_KEY` — required for AG2 agents

Optional (web search):
- `TAVILY_API_KEY` — Tavily search API key. Sign up at https://tavily.com.
- `SEARXNG_BASE_URL` — URL of a running SearXNG instance (e.g. `http://localhost:8080`).

If neither search credential is provided the example runs with a stub that
returns representative placeholder results, so you can verify the full
agent-conversation flow without search credentials.

## Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/BrainBlend-AI/atomic-agents
   cd atomic-agents
   ```

2. Navigate to this example:
   ```bash
   cd atomic-examples/ag2-orchestration
   ```

3. Install dependencies:

   **Using uv (recommended for this monorepo):**
   ```bash
   uv sync
   ```

   **Using pip:**
   ```bash
   pip install "atomic-agents" "ag2[openai]>=0.11.2,<1.0" sympy requests python-dotenv
   ```

4. Set environment variables. Create a `.env` file in the `ag2-orchestration`
   directory:
   ```env
   OPENAI_API_KEY=sk-...

   # Optional — for real web search (leave blank to use stub)
   TAVILY_API_KEY=tvly-...
   SEARXNG_BASE_URL=http://localhost:8080
   ```

## How to run

```bash
# From the ag2-orchestration directory:
python main.py

# Or with uv:
uv run python main.py
```

Expected output: the GroupChat conversation prints to the console, ending when
`AnalystAgent` says `TERMINATE`. Typically 4–6 rounds.

## Key concepts

### Why combine AG2 and Atomic Agents?

| Concern | AG2 | Atomic Agents |
|---|---|---|
| Multi-agent coordination | ✅ GroupChat, speaker selection | — |
| Termination logic | ✅ `is_termination_msg` | — |
| Typed tool I/O | — | ✅ `BaseTool[Input, Output]` |
| Runtime schema validation | — | ✅ Pydantic v2 |
| Structured output | — | ✅ `BaseIOSchema` |
| LLM provider abstraction | ✅ `LLMConfig` | ✅ Instructor |

Using both frameworks together means AG2 agents receive structured, validated
JSON from every tool call — not raw strings — which significantly reduces
hallucination of tool results.

### `BaseIOSchema`

All data flowing through Atomic Agents tools inherits from `BaseIOSchema`
(a Pydantic `BaseModel` subclass). Validation happens on construction, so
malformed inputs fail fast with clear error messages before any API call is made.

### `BaseTool[InputSchema, OutputSchema]`

The generic `BaseTool` class enforces type-safe contracts between callers and
implementations. Subclass it, implement `run()`, and the framework handles the
rest:

```python
class WebSearchTool(BaseTool[SearchInput, SearchOutput]):
    def run(self, params: SearchInput) -> SearchOutput:
        ...
```

## References

- [AG2 documentation](https://docs.ag2.ai)
- [Atomic Agents documentation](https://atomicagents.ai)
- [AG2 GroupChat guide](https://docs.ag2.ai/docs/topics/groupchat/customized_speaker_selection)
- [Atomic Agents tools guide](https://atomicagents.ai/guides/tools)
