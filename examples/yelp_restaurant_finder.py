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
from atomic_agents.lib.tools.yelp_restaurant_finder_tool import YelpSearchTool, YelpSearchToolConfig, YelpSearchToolInputSchema

#######################
# AGENT CONFIGURATION #
#######################
# Define system prompt information
system_prompt_generator = SystemPromptGenerator(
    background=[
        "This assistant is a restaurant finder AI designed to help users find the best restaurants based on their preferences by asking clarifying questions.",
    ],
    steps=[
        "Greet the user and introduce yourself as a restaurant finder assistant.",
        "Inspect the required Yelp schema and identify the necessary filters.",
        "Ask the user questions to gather information for each filter until all required information is clear.",
        "Use the chat responses to gather all necessary information from the user.",
        "Once all required information is gathered, use the YelpSearchTool schema to search Yelp for restaurants.",
        "Summarize the search results and provide recommendations to the user.",
    ],
    output_instructions=[
        "Always think in steps before answering using internal reasoning.",
        "Provide helpful and relevant information to assist the user.",
        "Be friendly and respectful in all interactions.",
        "Ensure that the chat responses are used to ask clarifying questions and gather information, and the Yelp schema is used to perform the actual search.",
    ],
)

# Initialize chat memory
memory = AgentMemory()
initial_memory = [
    {
        "role": "assistant",
        "content": "Hello! I'm your restaurant finder assistant. How can I help you find a great place to eat today?",
    }
]
memory.load(initial_memory)

# Initialize the console
console = Console()

# Initialize the OpenAI client
client = instructor.from_openai(openai.OpenAI())

# Initialize the YelpSearchTool
yelp_tool = YelpSearchTool(YelpSearchToolConfig(api_key=os.getenv("YELP_API_KEY"), max_results=10))


######################
# SCHEMA DEFINITIONS #
######################
class ChatOutputSchema(BaseIOSchema):
    """This schema defines a markdown-enabled chat output."""

    markdown_output: str = Field(..., description="The answer to the question in markdown format.")


class OutputSchema(BaseIOSchema):
    """
    Output schema for the agent.

    This schema defines the structure of the agent's output, including its internal reasoning
    and the next action it plans to take.
    """

    internal_reasoning: List[str] = Field(
        ..., description="A list of strings representing the agent's step-by-step thought process leading to its decision."
    )
    action: Union[ChatOutputSchema, YelpSearchToolInputSchema] = Field(
        ...,
        description="The next action to be taken by the agent. This can be either a chat response (ChatOutputSchema) or a Yelp search request (YelpSearchToolInputSchema), depending on whether the agent needs to communicate with the user or perform a restaurant search.",
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
console.print("Restaurant Finder Agent is ready.")
console.print(f'Agent: {initial_memory[0]["content"]}')

while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit"]:
        print("Exiting chat...")
        break

    response = agent.run(agent.input_schema(chat_message=user_input))

    if isinstance(response.action, YelpSearchToolInputSchema):
        search_results = yelp_tool.run(response.action)

        agent.memory.add_message(
            "assistant",
            f"INTERNAL THOUGHT: I have found the following restaurants: {search_results.results}\n\n I will now summarize the results for the user.",
        )
        output = agent.run().action.markdown_output
    else:
        output = response.action.markdown_output

    console.print(f"Agent: {output}")
