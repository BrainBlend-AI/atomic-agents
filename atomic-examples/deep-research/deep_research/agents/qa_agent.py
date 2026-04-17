"""
QAAgent — answers a user's question directly from the accumulated ResearchState.

The writer produces long-form cited reports; the QA agent is the
conversational counterpart, for when the decider has ruled that the
state already contains enough material to answer. Its job is a tight,
cited reply plus a few follow-up questions to keep the conversation
moving.

Like the writer, every factual sentence must end with a ``[Sn]``
citation marker referencing a source in the state. Uncited factual
claims are not allowed — if the state doesn't support the answer, the
decider should have routed to a new research pass instead.
"""

import instructor
import openai
from pydantic import Field

from atomic_agents import AgentConfig, AtomicAgent, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator

from deep_research.config import ChatConfig


class QAInput(BaseIOSchema):
    """Input schema for the QAAgent."""

    question: str = Field(..., description="The user's question or follow-up.")


class QAOutput(BaseIOSchema):
    """Output schema for the QAAgent."""

    answer: str = Field(
        ...,
        description=(
            "Markdown-formatted answer. Every factual sentence must end with a [Sn] citation marker "
            "referencing a source from the research state."
        ),
    )
    follow_up_questions: list[str] = Field(
        ...,
        description="2–3 natural follow-up questions the user might want to ask next.",
    )


qa_agent = AtomicAgent[QAInput, QAOutput](
    AgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=ChatConfig.api_key)),
        model=ChatConfig.model,
        model_api_parameters={"reasoning_effort": ChatConfig.reasoning_effort},
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are a research assistant. You answer user questions using ONLY the sources and learnings "
                "already present in the research state (provided in your system context).",
                "You are the conversational counterpart to the long-form writer — shorter, tighter, same citation rules.",
            ],
            steps=[
                "Read the research state — sources and learnings — from the system context.",
                "Compose a concise markdown answer grounded in the learnings. Cite each factual sentence as [Sn].",
                "Suggest 2–3 follow-up questions that naturally extend the conversation.",
            ],
            output_instructions=[
                "Only cite source IDs that actually exist in the research state.",
                "If you cannot answer from the state, say so briefly rather than inventing claims.",
                "Keep the answer tight — a few short paragraphs, not a full report.",
                "Follow-up questions should be self-contained and phrased as the user would ask them.",
            ],
        ),
    )
)
