---
name: review
description: Review Atomic Agents code against framework-specific correctness, security, and style rules. Use when the user asks to "review", "audit", "check", or "validate" code that uses `atomic_agents` — before committing, before a PR, or when investigating misbehavior in an existing agent, tool, schema, context provider, or orchestration. Complements generic code review by focusing only on Atomic-Agents-specific concerns.
---

# Atomic Agents Code Review

This skill reviews code for correctness *with respect to the Atomic Agents framework*. It does not replace generic linting, type checking, or architectural review — it adds the framework-specific layer on top.

## Scope

Default to reviewing the current diff (`git diff` against the base branch). If there is no diff, review files the user points at.

Skip issues that are not specific to Atomic Agents (naming style, formatting, general Python conventions) — a generic reviewer covers those.

## Checklist

Work through the categories below in order. Raise an issue only at ≥75% confidence. Mark each issue with its category, file path, line, and a ready-to-apply fix.

### 1. Schemas (`BaseIOSchema`)

- Inherits from `BaseIOSchema`, not `pydantic.BaseModel`.
- Has a non-empty class docstring. The framework raises `ValueError` at import otherwise.
- Every field has `description=`. Instructor uses field descriptions when prompting.
- Types are appropriately constrained: `Literal` for closed sets, numeric bounds via `ge`/`le`, string/list lengths where meaningful.
- Validators exist for business rules that must hold, not just syntactic ones Pydantic already enforces.
- `Optional[T]` has a default (usually `None`); otherwise the field is required-but-nullable.

### 2. Agents (`AtomicAgent`)

- Constructed with explicit generic parameters: `AtomicAgent[In, Out](config=...)`.
- `AgentConfig.client` is an instructor-wrapped client (`instructor.from_openai(...)`, `instructor.from_anthropic(...)`, etc.), not a raw provider SDK client.
- `model` is set and appropriate for the task (not a reasoning model for trivial work, not a weak model for hard reasoning).
- `history` is present when the agent needs multi-turn state; absent when each call is independent.
- `assistant_role="model"` for Gemini, `"assistant"` elsewhere.
- `mode` matches the provider (`Mode.TOOLS` for OpenAI/Anthropic, `Mode.JSON` for Groq/Ollama/MiniMax, `Mode.GENAI_TOOLS` for Gemini).
- Provider-specific required params present: `max_tokens` for Anthropic, `reasoning_effort` for reasoning models as intended.

### 3. Tools (`BaseTool`)

- Declared with generic parameters: `class MyTool(BaseTool[In, Out])`. No legacy `input_schema = ...` / `output_schema = ...` class attributes.
- `run()` returns the output schema instance, not a dict or primitive.
- External I/O has a timeout.
- Retries/backoff on transient errors when the caller cannot reasonably retry.
- Credentials come from environment, not hardcoded.
- Routine failures (not-found, rate-limited) become typed outputs, not exceptions.

### 4. Context providers (`BaseDynamicContextProvider`)

- Registered on the agent before any `run()` that depends on them.
- `get_info()` returns a string, is fast, does no blocking I/O.
- Slow data sources (DB schemas, remote calls) are cached with a TTL inside the provider.
- Titles are unique across providers registered on the same agent.
- No secrets in `get_info()` output — it ends up in every LLM request.

### 5. System prompts (`SystemPromptGenerator`)

- Three sections used as intended: `background` = who, `steps` = how, `output_instructions` = format/constraints.
- No runtime facts hardcoded in `background` — those belong in context providers.
- Sections short enough that the model attends to all of them.

### 6. Orchestration

- Parallel agents don't share a `ChatHistory`.
- Router agents return a discriminated union, not free-text topics.
- Supervisor loops have an explicit iteration cap.
- Pipeline stages agree on types; where they don't, a typed adapter is present.

### 7. Security

- No `os.environ[...]` lookups that silently default to empty strings without a startup check.
- No secrets in docstrings, `description=` fields, logs, or context provider output.
- User input flowing into shell-out tools is validated or escaped.
- No `eval`/`exec` on model output.

### 8. Hooks

- Error paths use `register_hook("parse:error", ...)` / `register_hook("completion:error", ...)` instead of blanket `try/except` around `run()`.
- Hook handlers themselves don't raise — they log/meter and return.

### 9. Testing

- Unit tests don't hit real providers by default. If they can, there is a guard (env var or offline mock).
- Integration tests cap `max_tokens`.

## Output format

```
## Atomic Agents Review

**Files reviewed**: <paths>
**Issues**: <N critical>, <M important>, <K suggestions>

### Critical (must fix)

- <category> · `<path>:<line>` · <confidence>%
  <one-sentence problem>
  **Fix**
  ```python
  <ready-to-apply patch>
  ```

### Important (should fix)
<same shape>

### Suggestions
<same shape>

### Passed
- <brief list of framework invariants the code honors>
```

Keep each issue short. The caller already has the codebase; they do not need a re-explanation of the rule — just the pointer and the fix. For deep context on *why* a rule exists, link into the `framework` skill's reference files rather than duplicating content:

- Schemas: see `framework/references/schemas.md`
- Agents: see `framework/references/agents.md`
- Tools: see `framework/references/tools.md`
- Context providers: see `framework/references/context-providers.md`
- Prompts: see `framework/references/prompts.md`
- Orchestration: see `framework/references/orchestration.md`
- Providers: see `framework/references/providers.md`

## Review principles

- Confidence ≥75 only. Noise kills trust in the review.
- No pre-existing issues — review the *diff* unless told otherwise.
- Every issue has a concrete fix in the same format the code is written.
- Prefer fewer, sharper findings over exhaustive lists.
- Flag security issues at any confidence ≥50.
