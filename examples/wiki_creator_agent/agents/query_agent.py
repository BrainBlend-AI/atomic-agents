# File: query_agent.py

import instructor
import openai
from pydantic import BaseModel, Field
from typing import List
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator


class QueryAgentInputSchema(BaseIOSchema):
    """This schema defines the input schema for the QueryAgent."""

    instruction: str = Field(..., description="The user's input or question for which queries need to be generated.")
    num_queries: int = Field(default=5, description="The number of queries to generate.")


class QueryAgentOutputSchema(BaseIOSchema):
    """This schema defines the output schema for the QueryAgent."""

    queries: List[str] = Field(..., description="A list of generated queries based on the user's input.")


# Create the query agent
query_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI()),
        model="gpt-4o-mini",
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an expert google query generator.",
                "Your task is to generate relevant and diverse google search queries based on the user's input or question.",
            ],
            steps=[
                "Analyze the user's input or question.",
                "Generate a specified number of relevant google search queries.",
                "Ensure the queries cover different aspects of the user's input.",
            ],
            output_instructions=[
                "Generate clear and concise google queries.",
                "Ensure each google query is directly relevant to the user's input.",
                "Avoid repetitive queries and aim for diversity in the generated set.",
            ],
        ),
        input_schema=QueryAgentInputSchema,
        output_schema=QueryAgentOutputSchema,
    )
)
