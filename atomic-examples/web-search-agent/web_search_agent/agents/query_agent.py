import instructor
import openai
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

from web_search_agent.tools.searxng_search import SearxNGSearchTool


class QueryAgentInputSchema(BaseIOSchema):
    """This is the input schema for the QueryAgent."""

    instruction: str = Field(..., description="A detailed instruction or request to generate deep research queries for.")
    num_queries: int = Field(..., description="The number of queries to generate.")


query_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI()),
        model="gpt-4o-mini",
        system_prompt_generator=SystemPromptGenerator(
            background=[
                "You are an intelligent query generation expert.",
                "Your task is to generate a specified number of diverse and highly relevant queries based on a given instruction or request.",
                "The queries should cover different aspects of the instruction to ensure comprehensive exploration.",
            ],
            steps=[
                "You will receive a detailed instruction or request and the number of queries to generate.",
                "Generate the requested number of queries in a JSON format.",
            ],
            output_instructions=[
                "Ensure clarity and conciseness in each query.",
                "Ensure each query is unique and as diverse as possible while remaining relevant to the instruction.",
            ],
        ),
        input_schema=QueryAgentInputSchema,
        output_schema=SearxNGSearchTool.input_schema,
    )
)
