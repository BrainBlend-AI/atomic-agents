---
name: framework
description: Guide for the Atomic Agents Python framework — schemas, agents, tools, context providers, prompts, orchestration, and provider configuration. Use when code imports from `atomic_agents`, defines an `AtomicAgent`, `BaseTool`, or `BaseIOSchema`, or the user asks about multi-agent orchestration or LLM-provider wiring in an atomic-agents project.
---

# Atomic Agents Framework

Atomic Agents is a lightweight Python framework for building LLM applications with typed, structured input and output. It layers on top of [Instructor](https://python.useinstructor.com) and Pydantic so every interaction between user, agent, tool, and context is a validated schema.

This skill orients Claude on the framework and routes to focused reference files as the task requires.

## Core abstractions

| Concept | Class | Role |
|---|---|---|
| Schema | `BaseIOSchema` | Typed input/output contract — every agent/tool I/O is one |
| Agent | `AtomicAgent[In, Out]` | LLM-backed transformer from input schema to output schema |
| Config | `AgentConfig` | Wires client, model, history, prompt, roles, API params |
| Prompt | `SystemPromptGenerator` | Three-section prompt: background, steps, output_instructions |
| History | `ChatHistory` | Conversation state, serializable, token-counted |
| Tool | `BaseTool[In, Out]` | Deterministic capability the agent can invoke |
| Context | `BaseDynamicContextProvider` | Dynamic section injected into the system prompt at runtime |

All communication between these uses `BaseIOSchema` subclasses with **docstring-required** descriptions.

## Canonical imports

```python
from atomic_agents import (
    AtomicAgent, AgentConfig,
    BasicChatInputSchema, BasicChatOutputSchema,
    BaseIOSchema, BaseTool, BaseToolConfig,
)
from atomic_agents.context import (
    ChatHistory, Message,
    SystemPromptGenerator, BaseDynamicContextProvider,
)
# Optional: MCP interop
from atomic_agents.connectors.mcp import fetch_mcp_tools, MCPTransportType
```

Do not use legacy paths like `atomic_agents.lib.base.*` or `atomic_agents.agents.base_agent` — those were retired. Import from the top-level package where possible.

## Minimum viable agent

```python
import os, instructor, openai
from atomic_agents import AtomicAgent, AgentConfig, BasicChatInputSchema, BasicChatOutputSchema
from atomic_agents.context import ChatHistory

client = instructor.from_openai(openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"]))

agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](
    config=AgentConfig(
        client=client,
        model="gpt-5-mini",
        history=ChatHistory(),
    )
)

reply = agent.run(BasicChatInputSchema(chat_message="Hello"))
print(reply.chat_message)
```

`AtomicAgent` and `BaseTool` use PEP 695 generics — the type parameters carry runtime information, so write them explicitly and keep them accurate. Full runnable version: `atomic-examples/quickstart/quickstart/1_0_basic_chatbot.py`.

## Decision routing

Pick the reference file that matches the task. Each is loaded only when read.

| Task | Reference |
|---|---|
| Design or validate an input/output schema | [references/schemas.md](references/schemas.md) |
| Build, configure, or run an agent | [references/agents.md](references/agents.md) |
| Write a tool the agent will invoke | [references/tools.md](references/tools.md) |
| Inject dynamic data into the system prompt | [references/context-providers.md](references/context-providers.md) |
| Structure the system prompt | [references/prompts.md](references/prompts.md) |
| Coordinate multiple agents | [references/orchestration.md](references/orchestration.md) |
| Manage conversation state and multi-agent memory | [references/memory.md](references/memory.md) |
| Register telemetry, retries, or logging | [references/hooks.md](references/hooks.md) |
| Swap LLM provider or configure roles | [references/providers.md](references/providers.md) |
| Decide the project layout or `pyproject.toml` | [references/project-structure.md](references/project-structure.md) |
| Write tests for agents and tools | [references/testing.md](references/testing.md) |

When a concept is unclear, start from the user's verb: *create a schema* → schemas, *hook up a weather API* → tools, *inject user name into prompt* → context providers, *route between agents* → orchestration.

## Working style

Follow these defaults unless the project says otherwise. The reference files go deeper on each.

**Schemas are the contract.** Design the `BaseIOSchema` pair before writing the agent. Field descriptions flow into the LLM prompt via Instructor, so write them for the model, not just the developer. Every subclass needs a non-empty docstring — the framework enforces this at class-definition time.

**System prompts have three sections.** Use `SystemPromptGenerator(background=..., steps=..., output_instructions=...)`. Put persona in `background`, the ordered procedure in `steps`, and output-format rules in `output_instructions`. The agent falls back to a sensible default when omitted.

**Wrap the provider client with Instructor.** Always. `instructor.from_openai(...)`, `instructor.from_anthropic(...)`, `instructor.from_genai(...)` — without this the agent cannot enforce output schemas.

**Use `model_api_parameters` for provider knobs.** `temperature`, `max_tokens`, `reasoning_effort`, etc. live in the `model_api_parameters` dict on `AgentConfig`, not on the agent itself.

**Errors and retries flow through hooks.** Register handlers for `parse:error`, `completion:error`, `completion:last_attempt` rather than wrapping `run()` in try/except. See `references/hooks.md`.

**Tools return the output schema on success.** Failure should surface as validation errors or typed result schemas the caller pattern-matches on — don't raise through `run()` unless the failure is truly unrecoverable.

## When the user is starting from nothing

Scaffolding a brand-new project (fresh directory, `pyproject.toml`, first agent) is handled by the sibling skill `new-app`. Suggest it when the user says "new project", "start from scratch", or equivalent.

When reviewing or auditing existing code, the sibling skill `review` applies the Atomic-Agents-specific checklist.

## Versioning and compatibility

- Python 3.12+ (PEP 695 generics are used internally).
- Instructor 1.14+ with provider extras (`instructor[openai]`, `instructor[anthropic]`, etc.) — the workspace uses Instructor's extras to pull provider SDKs.
- Pydantic 2.
- For MCP interop, see `atomic_agents.connectors.mcp` — `fetch_mcp_tools`, `MCPFactory`, `MCPTransportType` are stable.

## Anti-patterns (surface these in review)

- Plain `BaseModel` instead of `BaseIOSchema`.
- Missing docstrings on `BaseIOSchema` subclasses (framework raises at import).
- `Field(..., description="...")` missing — Instructor leans on descriptions for prompt generation.
- Raw provider client (not wrapped in Instructor).
- Hardcoded API keys instead of env vars.
- Unbounded `ChatHistory` on long-running sessions.
- Blocking I/O inside `BaseDynamicContextProvider.get_info()` — it runs on every `agent.run()`.
- Catching `ValidationError` to hide schema problems instead of fixing descriptions or constraints.
- `MCPTransportType.STREAMABLE_HTTP` — the correct value is `HTTP_STREAM`.
- `ChatHistory.load(...)` called as a classmethod — it is an instance method that mutates self.

For deeper guidance load the relevant reference file above. For code-review runs, switch to the `review` skill.
