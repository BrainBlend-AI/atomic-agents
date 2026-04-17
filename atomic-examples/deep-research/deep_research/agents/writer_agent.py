"""
WriterAgent — turns the accumulated research state into a cited report.

Runs twice: the first call produces a draft, the second is a cheap
verification pass that rejects any sentence whose citation marker
(``[S3]`` etc.) doesn't correspond to a real source in the state.
This is the single trick that separates our writer from the typical
open-source "deep research" agent — it guarantees every claim in the
output is backed by a registered source.

Both passes use the same agent (same schema, same prompt) but with a
different input mode — see ``WriterMode``.
"""

from typing import Literal

import instructor
import openai
from pydantic import Field

from atomic_agents import AgentConfig, AtomicAgent, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator

from deep_research.config import ChatConfig

WriterMode = Literal["draft", "verify"]


class WriterInput(BaseIOSchema):
    """Input schema for the WriterAgent."""

    question: str = Field(..., description="The original research question.")
    mode: WriterMode = Field(
        ...,
        description=(
            "'draft' to compose the report from scratch using the research state; "
            "'verify' to rewrite an existing draft, removing any sentence whose citation doesn't match a real source."
        ),
    )
    draft: str = Field(
        "",
        description="When mode='verify', the draft to audit. Leave blank for mode='draft'.",
    )


class WriterOutput(BaseIOSchema):
    """Output schema for the WriterAgent."""

    report: str = Field(
        ...,
        description=(
            "Markdown report. Every non-trivial sentence must end with one or more citation markers "
            "like [S1] or [S2, S5], referencing sources by ID."
        ),
    )
    headline: str = Field(..., description="One-sentence top-line takeaway.")


writer_agent = AtomicAgent[WriterInput, WriterOutput](
    AgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=ChatConfig.api_key)),
        model=ChatConfig.model,
        model_api_parameters={"reasoning_effort": ChatConfig.reasoning_effort},
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are a research writer. You compose cited markdown reports from a structured research state "
                "provided in your system context (sources with IDs, and learnings grouped by sub-topic).",
            ],
            steps=[
                "In 'draft' mode:",
                "  1. Read the research state (sources and learnings) from the system context.",
                "  2. Organise the report with one section per sub-topic, in a logical order.",
                "  3. Every factual sentence cites the source(s) it's based on using [S1] / [S2, S4] markers.",
                "  4. End with a '## Sources' section. Format each entry as a bullet list: `- [Sn]: <title> — <url>`. Do NOT append a trailing [Sn] after the URL.",
                "In 'verify' mode:",
                "  1. Read the draft provided in the input.",
                "  2. Remove any sentence that carries a citation marker not present in the research state's sources.",
                "  3. Remove any factual sentence with no citation at all.",
                "  4. Return the cleaned report verbatim otherwise — do not paraphrase, do not add new material.",
            ],
            output_instructions=[
                "Use markdown headings (## per sub-topic).",
                "Only cite source IDs that actually exist in the provided research state.",
                "The headline is one sentence, max 20 words, and stands on its own.",
            ],
        ),
    )
)
