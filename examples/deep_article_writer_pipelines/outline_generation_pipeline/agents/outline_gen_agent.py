# outline_gen_agent.py
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
import instructor
import openai


class OutlineAgentInputSchema(BaseIOSchema):
    """
    Input schema for the Outline Generation Agent.
    This schema defines the input structure for generating an article outline.
    """

    instruction: str = Field(..., description="The main topic or instruction for the article.")
    search_results: list = Field(..., description="A list of search results to use as reference for creating the outline.")


class OutlineAgentOutputSchema(BaseIOSchema):
    """
    Output schema for the Outline Generation Agent.
    This schema defines the structure of the generated article outline.
    """

    reasoning_and_analysis: list[str] = Field(..., description="A list of reasoning and analysis steps for the outline.")
    article_title: str = Field(..., description="The title of the article.")
    section_titles: list[str] = Field(
        ..., description="A list of sections for the article, excluding introduction and conclusion."
    )


outline_gen_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI()),
        model="gpt-4o-mini",
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an expert article outline generator.",
                "Your task is to create a comprehensive outline for an article based on a given topic and search results.",
            ],
            steps=[
                "Analyze the given instruction and search results.",
                "Generate a catchy and informative article title.",
                "Generate 3-5 sections, excluding introduction and concluding sections.",
            ],
            output_instructions=[
                "Provide an article title that accurately reflects the main topic.",
                "Ensure the section titles are clear, concise, and logically ordered.",
                "Do NOT include an introduction or conclusion in the section titles.",
                "Provide a list of reasoning and analysis steps that led to your outline decisions.",
            ],
        ),
        input_schema=OutlineAgentInputSchema,
        output_schema=OutlineAgentOutputSchema,
    )
)
