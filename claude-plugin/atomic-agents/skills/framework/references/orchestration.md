# Orchestration Patterns

## Contents
- Pattern selector
- Single agent
- Sequential pipeline
- Parallel fan-out
- Router
- Supervisor / validate-and-retry
- Search + execute (large tool surface)
- Shared context between agents
- Common mistakes

## Pattern selector

| Situation | Pattern | Working example |
|---|---|---|
| One transformation, no collaboration | Single agent | `atomic-examples/quickstart/` |
| Stages where each refines the last | Sequential pipeline | `atomic-examples/deep-research/` |
| Independent lookups that can run at the same time | Parallel fan-out | — |
| Classify request, then route to specialized agent | Router | `atomic-examples/orchestration-agent/` |
| Quality gate / iterative refinement | Supervisor | — |
| Large tool catalog (dozens+) | Search + execute | `atomic-examples/progressive-disclosure/` |

Pick one, start minimal, compose only when the simpler shape stops working.

## Single agent

Already the default. Shown here for completeness:

```python
reply = agent.run(MyInput(...))
```

## Sequential pipeline

Each stage's output is the next stage's input. Types line up — Python checks it statically, the LLM runtime catches misalignments.

```python
extracted = extractor.run(RawDoc(text=doc))          # RawDoc -> Entities
scored    = scorer.run(ScoreQuery(entities=extracted.entities))
summary   = summarizer.run(SummaryReq(scored=scored))
```

Use typed adapters when shapes don't align:

```python
def entities_to_score_query(e: Entities) -> ScoreQuery:
    return ScoreQuery(entities=e.entities, threshold=0.7)
```

## Parallel fan-out

For independent lookups, `asyncio.gather`:

```python
import asyncio

async def enrich(query):
    docs_task   = asyncio.create_task(doc_agent.run_async(DocLookup(q=query)))
    users_task  = asyncio.create_task(user_agent.run_async(UserLookup(q=query)))
    docs, users = await asyncio.gather(docs_task, users_task)
    return await summary_agent.run_async(Summary(docs=docs.items, users=users.items))
```

Each agent gets its own `ChatHistory` (or none at all). Sharing `ChatHistory` across concurrent agents corrupts state.

## Router

One agent classifies, others handle. Model the classification as a discriminated output:

```python
from typing import Literal, Union
from pydantic import Field

class BillingRoute(BaseIOSchema):
    """Route to the billing agent."""
    topic: Literal["billing"] = "billing"
    normalized_question: str = Field(..., description="Rewritten for the billing agent.")

class TechRoute(BaseIOSchema):
    """Route to the tech-support agent."""
    topic: Literal["tech"] = "tech"
    normalized_question: str = Field(..., description="Rewritten for the tech-support agent.")

class Routing(BaseIOSchema):
    """Routing decision."""
    choice: Union[BillingRoute, TechRoute] = Field(..., description="Routed agent and payload.")

router = AtomicAgent[UserQuery, Routing](config=router_cfg)

decision = router.run(query)
if isinstance(decision.choice, BillingRoute):
    reply = billing_agent.run(...)
else:
    reply = tech_agent.run(...)
```

## Supervisor / validate-and-retry

Useful when a second LLM pass validates the first. The supervisor returns a typed verdict; loop until the verdict is "accept".

```python
draft = writer.run(DraftRequest(topic="Atomic Agents"))
for _ in range(3):
    verdict = reviewer.run(ReviewReq(draft=draft.text))
    if verdict.accept:
        break
    draft = writer.run(DraftRequest(topic="Atomic Agents", revise_notes=verdict.notes))
```

Cap the loop — a bad prompt can oscillate forever.

## Search + execute (large tool surface)

When the agent has access to many tools (dozens or hundreds, e.g. MCP server with a big API), exposing them all blows up the prompt. Split into two tools: `search_actions(intent) -> [candidate_ids]` and `execute_action(id, args)`.

```python
class SearchActions(BaseIOSchema):
    """Find candidate actions by intent."""
    intent: str = Field(..., description="Natural-language intent.")

class ActionCandidates(BaseIOSchema):
    """Matched action IDs."""
    ids: list[str] = Field(..., description="Ordered by relevance.")

class ExecuteAction(BaseIOSchema):
    """Run a specific action by ID."""
    id: str = Field(..., description="Action ID from search.")
    args: dict = Field(default_factory=dict, description="JSON-shaped args.")
```

The host holds the full catalog internally. The LLM only sees the two tools. Context stays lean. Full implementation (three MCP servers, 24 tools, ~92% token reduction on definitions) in `atomic-examples/progressive-disclosure/`.

## Shared context between agents

Register the same provider instance on multiple agents. Updates propagate:

```python
session = SessionCtx()
router.register_context_provider("session", session)
billing_agent.register_context_provider("session", session)
tech_agent.register_context_provider("session", session)
```

This is cheaper than passing session state through every schema.

## Common mistakes

- Sharing `ChatHistory` between parallel agents — races and stale messages.
- Hidden coupling between agents via file paths or globals — put shared state behind a context provider or explicit schema.
- Router that returns a free-text "topic" instead of a discriminated union — loses type safety.
- Supervisor loops with no upper bound — cap them.
- Sequential pipelines that silently drop fields between stages — use typed adapters.
