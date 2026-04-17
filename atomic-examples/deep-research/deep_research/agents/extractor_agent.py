"""
ExtractorAgent — pulls atomic claims out of one scraped source.

Called once per (sub-topic, source) pair. The orchestrator feeds in the
raw markdown content from the scraper and the agent returns a small
list of factual claims plus any follow-up questions the content raises.

We keep claims short and atomic so the writer can cite them individually
in the final report. The agent is deliberately *not* asked to assign
source IDs — the orchestrator already knows which source it passed in
and tags the claims before appending them to the state.
"""

import instructor
import openai
from pydantic import Field

from atomic_agents import AgentConfig, AtomicAgent, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator

from deep_research.config import ChatConfig


class ExtractorInput(BaseIOSchema):
    """Input schema for the ExtractorAgent."""

    sub_topic: str = Field(..., description="Which sub-topic the orchestrator is researching right now.")
    source_url: str = Field(..., description="The URL the content was scraped from (for citation context).")
    source_title: str = Field(..., description="The page's title.")
    content: str = Field(..., description="Raw scraped content in markdown form.")


class ExtractorOutput(BaseIOSchema):
    """Output schema for the ExtractorAgent."""

    claims: list[str] = Field(
        ...,
        description=(
            "Atomic, single-sentence factual claims relevant to the sub-topic. "
            "One claim per line. Skip anything that isn't directly supported by the content."
        ),
    )
    new_questions: list[str] = Field(
        ...,
        description=(
            "Follow-up questions the content surfaces that aren't yet answered. "
            "The reflector may turn these into next-round queries."
        ),
    )


extractor_agent = AtomicAgent[ExtractorInput, ExtractorOutput](
    AgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=ChatConfig.api_key)),
        model=ChatConfig.model,
        model_api_parameters={"reasoning_effort": ChatConfig.reasoning_effort},
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are a research analyst. You read one source at a time and extract the factual claims "
                "it makes that are relevant to the current sub-topic.",
            ],
            steps=[
                "Read the scraped content carefully.",
                "Extract claims that are (a) factual, (b) relevant to the sub-topic, (c) directly supported by the text.",
                "Note follow-up questions the content raises but doesn't answer.",
            ],
            output_instructions=[
                "Each claim must be a single, self-contained sentence.",
                "Do NOT include filler like 'according to the article' — just state the claim.",
                "Aim for 3–8 claims per source; fewer is fine if the source is thin.",
                "If the content is irrelevant or empty, return an empty claims list.",
            ],
        ),
    )
)
