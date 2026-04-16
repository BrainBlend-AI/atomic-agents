# System Prompts (`SystemPromptGenerator`)

## Contents
- Three-part structure
- Section-writing guidance
- Interaction with context providers
- Omitting sections
- Common mistakes

## Three-part structure

```python
from atomic_agents.context import SystemPromptGenerator

spg = SystemPromptGenerator(
    background=[
        "You are a senior SRE.",
        "You triage production alerts into severity-tagged summaries.",
    ],
    steps=[
        "Read the alert payload.",
        "Identify the failing component and blast radius.",
        "Rank severity as P0/P1/P2/P3.",
        "Suggest the next diagnostic step.",
    ],
    output_instructions=[
        "Answer in 4 sections: Summary, Severity, Cause, Next step.",
        "Keep each section to one sentence.",
    ],
)
```

The generator renders to the system prompt in that order: **background → steps → output_instructions → dynamic context provider blocks**.

## Section-writing guidance

**`background`** — persona and scope. *Who* the agent is and *what* it's for. Keep it short; long personas pull quality from the task itself.

**`steps`** — the ordered procedure. *How* to process the input. Imperative mood, one action per line, numbered optional.

**`output_instructions`** — format and quality constraints. *What* the response must look like. Edge-case behavior belongs here too: "Say 'I don't know' rather than guess."

Keep each list short. If the prompt sprawls past ~30 lines, either promote details into a reference file and mention it, or split into a second agent.

## Interaction with context providers

Providers render *after* the three static sections. Structure the prompt so context providers fill in the *runtime* facts the static prompt references:

```python
spg = SystemPromptGenerator(
    background=[
        "You are a calendar assistant for the current user.",
        "Use the User Context and Current Time blocks below when reasoning about schedules.",
    ],
    steps=[
        "Parse the request.",
        "Resolve relative dates using Current Time.",
        "Look up availability in Session.",
    ],
    output_instructions=["Reply in the user's locale from User Context."],
)

agent.register_context_provider("user", UserCtx())
agent.register_context_provider("time", TimeCtx())
agent.register_context_provider("session", SessionCtx())
```

See `context-providers.md`.

## Omitting sections

All three sections are optional. Pass `background=None` to skip it, etc. A `SystemPromptGenerator` with every section `None` produces an empty system prompt.

To disable the system prompt entirely, set `system_role=None` on `AgentConfig` — this suppresses the entire first message and is what some reasoning-focused OpenAI models prefer.

## Common mistakes

- Stuffing the task description into `background` instead of letting the user input carry it.
- Multi-sentence bullets — the model loses the structure. Split into multiple items.
- Contradictions between `steps` and `output_instructions` — always reconcile.
- Hardcoding runtime facts ("The current user is Alice") in `background` instead of using a context provider.
- Forgetting to update `steps` after adding a new context provider.
