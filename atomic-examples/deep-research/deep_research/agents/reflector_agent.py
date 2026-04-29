"""
ReflectorAgent — decides, after each depth iteration, whether to keep
researching the sub-topic or call it done.

Deep research's defining move. Without the reflector we'd either
over-search easy sub-topics (wasting tokens) or under-search hard ones
(producing a shallow report). The reflector looks at the learnings
gathered so far for the sub-topic and either says "good enough" or
emits the specific follow-up queries to run next.

The reflector sees the full state via the ``ResearchStateProvider``,
so it can judge sufficiency in light of what the neighbouring
sub-topics already cover.
"""

import instructor
import openai
from pydantic import Field

from atomic_agents import AgentConfig, AtomicAgent, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator

from deep_research.config import ChatConfig


class ReflectorInput(BaseIOSchema):
    """Input schema for the ReflectorAgent."""

    sub_topic: str = Field(..., description="The sub-topic being evaluated.")
    iterations_so_far: int = Field(
        ...,
        description="How many depth iterations have been completed for this sub-topic already.",
    )
    max_iterations: int = Field(
        ...,
        description="Hard cap. After this many iterations the orchestrator stops regardless of your decision.",
    )


class ReflectorOutput(BaseIOSchema):
    """Output schema for the ReflectorAgent."""

    reasoning: str = Field(..., description="One short paragraph explaining the decision.")
    sufficient: bool = Field(
        ...,
        description=(
            "True if the learnings for this sub-topic are rich enough to write a section of the report. "
            "False if more research is needed."
        ),
    )
    next_queries: list[str] = Field(
        ...,
        description=(
            "If sufficient is False, 2–3 new search queries that target the remaining gaps. "
            "If sufficient is True, return an empty list."
        ),
    )


reflector_agent = AtomicAgent[ReflectorInput, ReflectorOutput](
    AgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=ChatConfig.api_key)),
        model=ChatConfig.model,
        model_api_parameters={"reasoning_effort": ChatConfig.reasoning_effort},
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are a research editor. After each round of searching and extraction, you decide "
                "whether the current sub-topic has enough material to stand on its own in the final report.",
                "You have full visibility into the research state — sources, learnings, and the plan.",
            ],
            steps=[
                "Look only at the learnings tagged with the given sub-topic.",
                "Ask: could a reader write a coherent, cited section from this material?",
                "If yes: mark sufficient=true and return no queries.",
                "If no: identify the specific gap and produce 2–3 queries that target it.",
            ],
            output_instructions=[
                "Be decisive. 'Maybe' is never the right answer.",
                "Prefer marking sufficient=true once you have 4+ substantive, non-duplicate claims.",
                "Prefer marking sufficient=true on the final iteration regardless of coverage — the orchestrator will stop anyway.",
                "Next queries, if any, must be keywords-and-operators style, not sentences.",
            ],
        ),
    )
)
