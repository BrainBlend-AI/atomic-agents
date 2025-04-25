import instructor
import openai
from pydantic import Field
from typing import List
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator


class QueryAgentInputSchema(BaseIOSchema):
    """This is the input schema for the QueryAgent."""

    instruction: str = Field(..., description="A detailed instruction or request to generate deep research queries for.")
    num_queries: int = Field(..., description="The number of queries to generate.")


class QueryAgentOutputSchema(BaseIOSchema):
    """This is the output schema for the QueryAgent."""

    queries: List[str] = Field(..., description="A list of search queries.")


query_agent = BaseAgent[QueryAgentInputSchema, QueryAgentOutputSchema](
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI()),
        model="gpt-4o-mini",
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an advanced search query generator.",
                "Your task is to convert user questions into multiple effective search queries.",
            ],
            steps=[
                "Analyze the user's question to understand the core information need.",
                "Generate multiple search queries that capture the question's essence from different angles.",
                "Ensure each query is optimized for search engines (compact, focused, and unambiguous).",
            ],
            output_instructions=[
                "Generate 3-5 different search queries.",
                "Do not include special search operators or syntax.",
                "Each query should be concise and focused on retrieving relevant information.",
            ],
        ),
    )
)
