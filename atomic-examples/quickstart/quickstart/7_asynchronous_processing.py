import os
import asyncio
import instructor
import openai
from rich.console import Console
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgent, BaseAgentConfig, BaseAgentInputSchema
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

# API Key setup
API_KEY = ""
if not API_KEY:
    API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError(
        "API key is not set. Please set the API key as a static variable or in the environment variable OPENAI_API_KEY."
    )

# Initialize a Rich Console for pretty console outputs
console = Console()

# OpenAI client setup using the Instructor library
client = instructor.from_openai(openai.AsyncOpenAI(api_key=API_KEY))


# Define a schema for the output data
class PersonSchema(BaseIOSchema):
    """Schema for person information."""

    name: str
    age: int
    pronouns: list[str]
    profession: str


# System prompt generator setup
sysyem_prompt_generator = SystemPromptGenerator(
    background=["You parse a sentence and extract elements."],
    steps=[],
    output_instructions=[],
)

dataset = [
    "My name is Mike, I am 30 years old, my pronouns are he/him, and I am a software engineer.",
    "My name is Sarah, I am 25 years old, my pronouns are she/her, and I am a data scientist.",
    "My name is John, I am 40 years old, my pronouns are he/him, and I am a product manager.",
    "My name is Emily, I am 35 years old, my pronouns are she/her, and I am a UX designer.",
    "My name is David, I am 28 years old, my pronouns are he/him, and I am a web developer.",
    "My name is Anna, I am 32 years old, my pronouns are she/her, and I am a graphic designer.",
]

sem = asyncio.Semaphore(2)

# Agent setup with specified configuration
agent = BaseAgent[BaseAgentInputSchema, PersonSchema](
    config=BaseAgentConfig(client=client, model="gpt-4o-mini", sysyem_prompt_generator=sysyem_prompt_generator)
)


async def exec_agent(message: str):
    """Execute the agent with the provided message."""
    user_input = BaseAgentInputSchema(chat_message=message)
    agent.reset_memory()
    response = await agent.run_async(user_input)
    return response


async def process(dataset: list[str]):
    """Process the dataset asynchronously."""
    async with sem:
        # Run the agent asynchronously for each message in the dataset
        # and collect the responses
        responses = await asyncio.gather(*(exec_agent(message) for message in dataset))

    return responses


responses = asyncio.run(process(dataset))
console.print(responses)
