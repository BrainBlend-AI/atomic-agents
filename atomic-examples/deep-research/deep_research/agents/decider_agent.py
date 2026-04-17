"""
DeciderAgent — routes a follow-up user message to either more research or a direct answer.

In chat mode, every user turn after the first faces the same question:
do we already have the material to answer this, or do we need to go out
and gather more? This is that agent's entire job — one binary decision,
backed by short reasoning.

Deciding from the shared ``ResearchState`` (sources, learnings, plan)
instead of from the raw message keeps the decision grounded in what the
pipeline has actually collected, not what the model imagines it knows.
"""

import instructor
import openai
from pydantic import Field

from atomic_agents import AgentConfig, AtomicAgent, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator

from deep_research.config import ChatConfig


class DeciderInput(BaseIOSchema):
    """Input schema for the DeciderAgent."""

    user_message: str = Field(..., description="The user's latest question or follow-up.")


class DeciderOutput(BaseIOSchema):
    """Output schema for the DeciderAgent."""

    reasoning: str = Field(
        ...,
        description="One short paragraph: what's already in the state, what's missing, and why that tips the decision.",
    )
    needs_research: bool = Field(
        ...,
        description=(
            "True if a new research pass is needed — state is empty, irrelevant, stale, or missing a key angle. "
            "False if the existing learnings already cover what the user is asking."
        ),
    )


decider_agent = AtomicAgent[DeciderInput, DeciderOutput](
    AgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=ChatConfig.api_key)),
        model=ChatConfig.model,
        model_api_parameters={"reasoning_effort": ChatConfig.reasoning_effort, "temperature": 0.1},
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are a routing agent. Given the user's latest message and the current ResearchState "
                "(sources and learnings already gathered), you decide whether another research pass is warranted.",
                "You do NOT answer the question yourself. You only decide: research more, or hand off to the Q&A agent.",
            ],
            steps=[
                "Read the research state from the system context — what sources and learnings exist?",
                "Compare the user's message against those learnings. Is the answer already present, even partially?",
                "Flag a new research pass when state is empty, off-topic, outdated for a time-sensitive question, "
                "or missing an angle the user is now asking about.",
                "Otherwise, route to Q&A.",
            ],
            output_instructions=[
                "Be decisive. 'Maybe' is never the right answer.",
                "If the state is empty, always decide needs_research=true.",
                "For time-sensitive questions, check the current date in context and re-research if learnings look stale.",
                "Reasoning must cite concrete evidence from state (or its absence) — not vague intuition.",
            ],
        ),
    )
)
