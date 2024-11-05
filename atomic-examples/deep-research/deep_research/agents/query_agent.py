from deep_research.config import ChatConfig
import instructor
import openai
from pydantic import Field
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

from deep_research.tools.searxng_search import SearxNGSearchTool


class QueryAgentInputSchema(BaseIOSchema):
    """This is the input schema for the QueryAgent."""

    instruction: str = Field(..., description="A detailed instruction or request to generate search engine queries for.")
    num_queries: int = Field(..., description="The number of search queries to generate.")


query_agent = BaseAgent(
    BaseAgentConfig(
        client=instructor.from_openai(openai.OpenAI(api_key=ChatConfig.api_key)),
        model=ChatConfig.model,
        system_prompt_generator=SystemPromptGenerator(
            background=[
                (
                    "You are an expert search engine query generator with a deep understanding of which"
                    "queries will maximize the number of relevant results."
                )
            ],
            steps=[
                "Analyze the given instruction to identify key concepts and aspects that need to be researched",
                "For each aspect, craft a search query using appropriate search operators and syntax",
                "Ensure queries cover different angles of the topic (technical, practical, comparative, etc.)",
            ],
            output_instructions=[
                "Return exactly the requested number of queries",
                "Format each query like a search engine query, not a natural language question",
                "Each query should be a concise string of keywords and operators",
            ],
        ),
        input_schema=QueryAgentInputSchema,
        output_schema=SearxNGSearchTool.input_schema,
    )
)
