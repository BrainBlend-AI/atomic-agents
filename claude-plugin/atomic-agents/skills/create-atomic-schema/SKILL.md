---
name: create-atomic-schema
description: Design and write a `BaseIOSchema` input/output pair for an Atomic Agents agent or tool — docstrings, field descriptions, validators, error variants. Use when the user asks to "create a schema", "design the input/output schema", "define an `IOSchema`", "write a `BaseIOSchema`", "model the agent's output", or runs `/atomic-agents:create-atomic-schema`.
---

# Create an Atomic Agents Schema

Author a `BaseIOSchema` pair (input and/or output) that becomes the contract between an agent or tool and its caller. The framework enforces docstrings on every subclass, and Instructor flows field descriptions into the LLM prompt — so the schema **is** part of the prompt, not just typing.

For deep material (validators, discriminated unions, error envelopes), the authority is `../framework/references/schemas.md`. This skill is the action-oriented path: clarify → write → validate.

## When this fires vs the umbrella `framework` skill

- **This skill**: the user is creating or modifying a specific schema — e.g. "design the output schema for the planner agent", "add a field to `WeatherInput`", "split the result into success and failure variants".
- **`framework` skill**: the user is asking about Atomic Agents in general or doing something other than authoring schemas.

## Phase 1 — Clarify

Ask only what is not already obvious from context. Bundle into one message; do not interrogate one-at-a-time.

1. **Caller** — is this for an `AtomicAgent`, a `BaseTool`, both (an agent that emits a tool-input schema), or a nested sub-schema?
2. **Direction** — input only, output only, or a paired Input/Output?
3. **Fields** — what fields does the caller need, with which types? (Required vs optional, defaults, constraints.)
4. **Failure modes** — can this legitimately fail? If yes, plan a typed error variant rather than raising. See `../framework/references/schemas.md` → "Error-schema pattern".

If the user is mid-conversation about an existing schema, skip questions answered in context.

## Phase 2 — Write

Place schema(s) where they will be imported from. Conventional locations:

- `<project>/agents/<agent_name>/schemas.py` — agent-owned schemas
- `<project>/tools/<tool_name>_tool.py` — tool I/O lives next to the tool
- `<project>/schemas/<topic>.py` — schemas shared across multiple components

### Required ingredients on every schema

- Subclass `BaseIOSchema` (not `BaseModel`).
- A non-empty class docstring — the framework raises at import otherwise. Write it for the LLM, because Instructor uses it as the schema's `description`.
- Every `Field(...)` carries a `description=` written for the LLM.
- Use `Literal[...]` for closed sets before reaching for `Enum` — flatter JSON Schema, easier for Instructor.

### Minimal template

```python
from typing import Optional, Literal
from pydantic import Field
from atomic_agents import BaseIOSchema


class WeatherInput(BaseIOSchema):
    """A request for current weather conditions."""

    city: str = Field(..., description="City name, e.g. 'Brussels' or 'New York'.")
    units: Literal["metric", "imperial"] = Field(
        default="metric",
        description="Unit system for the temperature.",
    )


class WeatherOutput(BaseIOSchema):
    """Current weather conditions for a city."""

    status: Literal["ok", "error"] = Field(..., description="Outcome code.")
    temperature_c: Optional[float] = Field(
        default=None, description="Temperature in Celsius when status='ok'."
    )
    summary: Optional[str] = Field(
        default=None, description="Human-readable summary when status='ok'."
    )
    error: Optional[str] = Field(
        default=None, description="Failure message when status='error'."
    )
```

### When to add validators

- **Field-level** for normalization (lowercase, strip, enum coercion) and single-field validation.
- **Model-level** (`@model_validator(mode="after")`) for cross-field rules (start ≤ end, mutually exclusive flags).

Validation errors trigger Instructor retries and fire the `parse:error` hook — they're a feature, not a failure path. Do **not** swallow them.

### When to use discriminated unions

If the caller must exhaustively handle multiple result shapes, prefer a union over an inflated single schema:

```python
class SearchSuccess(BaseIOSchema):
    """Successful search result."""
    kind: Literal["ok"] = "ok"
    results: list[str] = Field(..., description="Matching items.")

class SearchFailure(BaseIOSchema):
    """Search could not complete."""
    kind: Literal["error"] = "error"
    code: Literal["rate_limited", "no_results", "upstream_error"] = Field(
        ..., description="Machine-readable failure code."
    )
    message: str = Field(..., description="Human-readable failure reason.")

class SearchOutput(BaseIOSchema):
    """Search outcome — success or typed failure."""
    result: SearchSuccess | SearchFailure = Field(..., description="Outcome.")
```

The `kind` discriminator on each variant lets Pydantic resolve the union without ambiguity.

## Phase 3 — Verify

Smoke-check the schema imports cleanly and round-trips through `model_json_schema()`:

```bash
uv run python -c "from <project>.<module> import WeatherInput, WeatherOutput; print(WeatherInput.model_json_schema()['title'])"
```

If the import raises `ValueError("… must have a non-empty docstring …")`, add the docstring. If a field's JSON schema is missing a description, add `description=` to its `Field(...)`.

## Phase 4 — Hand off

Tell the user:

- Where the schema lives and what to import.
- Next step in their flow:
  - Wiring it into an agent → `create-atomic-agent` skill.
  - Wiring it into a tool → `create-atomic-tool` skill.
  - Adding a context provider that depends on the same domain → `create-atomic-context-provider` skill.

## Anti-patterns to refuse on sight

- Plain `BaseModel` instead of `BaseIOSchema` — loses docstring enforcement and the JSON-schema overrides Instructor depends on.
- Missing class docstring — framework raises at import.
- `Field(...)` without `description=` — Instructor has nothing to tell the model about the field.
- `Optional[str]` with no default — required-but-nullable, which is rarely the intent.
- `dict`, `Any`, or `object` as a field type — the LLM produces anything and Pydantic cannot validate.
- Catching `ValidationError` to "make the agent more robust" — fix the field constraints or descriptions instead.

For deeper material — composition, nested schemas, discriminated unions in production, validator gotchas — load `../framework/references/schemas.md`.
