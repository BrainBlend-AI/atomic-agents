###########
# IMPORTS #
###########
import os
import logging
from typing import Union, List
from pydantic import BaseModel, Field
import instructor
import openai
from rich.console import Console

from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentOutputSchema, BaseAgentConfig, BaseIOSchema
from atomic_agents.lib.tools.search.searxng_tool import SearxNGTool, SearxNGToolConfig, SearxNGToolInputSchema

#######################
# AGENT CONFIGURATION #
#######################
# Define system prompt information
system_prompt_generator = SystemPromptGenerator(
    background=[
        "This assistant is a product finder AI designed to help users find products based on their preferences by asking clarifying questions.",
    ],
    steps=[
        "Greet the user and introduce yourself as a product finder assistant.",
        "Ask the user questions to gather information about the product they are looking for.",
        "Use the chat responses to gather all necessary information from the user.",
        "Once sufficient information is gathered, use the SearxNGTool to search for products.",
        "Summarize the search results and provide recommendations to the user.",
    ],
    output_instructions=[
        "Always think in steps before answering using internal reasoning.",
        "Provide helpful and relevant information to assist the user.",
        "Be friendly and respectful in all interactions.",
        "Ensure that the chat responses are used to ask clarifying questions and gather information, and the search tool is used to find products.",
    ],
)

# Initialize chat memory
memory = AgentMemory()
initial_memory = [
    {
        "role": "assistant",
        "content": "Hello! I'm your product finder assistant. What kind of product are you looking for today?",
    }
]
memory.load(initial_memory)

# Initialize the console
console = Console()

# Initialize the OpenAI client
client = instructor.from_openai(openai.OpenAI())

# Initialize the SearxNGTool
searxng_tool = SearxNGTool(SearxNGToolConfig(base_url=os.getenv("SEARXNG_BASE_URL"), max_results=5))


class ChatOutputSchema(BaseIOSchema):
    """This schema defines a markdown-enabled chat output."""

    markdown_output: str = Field(..., description="The answer to the question in markdown format.")


######################
# SCHEMA DEFINITIONS #
######################
class OutputSchema(BaseIOSchema):
    """
    Output schema for the agent.

    This schema defines the structure of the agent's output, including its internal reasoning
    and the next action it plans to take.
    """

    internal_reasoning: List[str] = Field(
        ..., description="A list of strings representing the agent's step-by-step thought process leading to its decision."
    )
    action: Union[ChatOutputSchema, SearxNGToolInputSchema] = Field(
        ...,
        description="The next action to be taken by the agent. This can be either a chat response (ChatOutputSchema) or a search request (SearxNGToolInputSchema), depending on whether the agent needs to communicate with the user or perform a product search.",
    )


# Create a config for the chat agent
agent_config = BaseAgentConfig(
    client=client,
    system_prompt_generator=system_prompt_generator,
    model="gpt-4o-mini",
    memory=memory,
    output_schema=OutputSchema,
)

# Create a chat agent
agent = BaseAgent(config=agent_config)

#############
# MAIN LOOP #
#############
console.print("Product Finder Agent is ready.")
console.print(f'Agent: {initial_memory[0]["content"]}')

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting chat...")
        break

    response = agent.run(agent.input_schema(chat_message=user_input))

    if isinstance(response.action, SearxNGToolInputSchema):
        search_results = searxng_tool.run(response.action)

        agent.memory.add_message(
            "assistant",
            f"INTERNAL THOUGHT: I have found the following products: {search_results.results}\n\n I will now summarize the results for the user.",
        )
        output = agent.run().action.markdown_output
    else:
        output = response.action.markdown_output

    console.print(f"Agent: {output}")
