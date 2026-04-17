"""
PlannerAgent — decomposes a research question into durable sub-topics.

Sub-topics are the *breadth* axis of the pipeline. They are decided once
by the planner and stay fixed; only the queries *within* a sub-topic
iterate as we learn more. Keeping the plan small and durable makes the
final report easy to organise section-by-section.

The planner runs before any state exists, so it takes only the raw
question and does not register any context providers.
"""

import instructor
import openai
from pydantic import Field

from atomic_agents import AgentConfig, AtomicAgent, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator

from deep_research.config import ChatConfig


class PlannerInput(BaseIOSchema):
    """Input schema for the PlannerAgent."""

    question: str = Field(..., description="The user's research question.")
    num_sub_topics: int = Field(
        ...,
        description="How many sub-topics to produce. 3–5 is a good range for a multi-page report.",
    )


class PlannedSubTopic(BaseIOSchema):
    """One entry in the research plan."""

    name: str = Field(
        ...,
        description="Short label (2–6 words), e.g. 'history and origins' or 'current applications'.",
    )
    initial_queries: list[str] = Field(
        ...,
        description="2–3 seed web-search queries to kick off this sub-topic. Keywords and operators, not full sentences.",
    )


class PlannerOutput(BaseIOSchema):
    """Output schema for the PlannerAgent."""

    sub_topics: list[PlannedSubTopic] = Field(
        ...,
        description="Sub-topics that together cover the research question without overlap.",
    )


planner_agent = AtomicAgent[PlannerInput, PlannerOutput](
    AgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=ChatConfig.api_key)),
        model=ChatConfig.model,
        model_api_parameters={"reasoning_effort": ChatConfig.reasoning_effort},
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are a research planner. Your job is to break a broad question into durable sub-topics.",
                "Good sub-topics are orthogonal (they don't overlap), collectively comprehensive, "
                "and each one can be researched independently of the others.",
            ],
            steps=[
                "Identify the core concept in the question.",
                "List the distinct angles a thorough report would need to cover "
                "(e.g. history, mechanics, applications, controversies, outlook — "
                "pick whatever is appropriate for the topic).",
                "Select the N most important angles, where N is the requested count.",
                "For each sub-topic, draft 2–3 seed search queries phrased as search-engine input.",
            ],
            output_instructions=[
                "Sub-topic names must be short (2–6 words).",
                "Initial queries must read like search-engine input, not natural-language sentences.",
                "Do not duplicate sub-topics or queries across the plan.",
            ],
        ),
    )
)
