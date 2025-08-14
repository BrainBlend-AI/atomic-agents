import os
import instructor
import openai
from rich.console import Console
from rich.text import Text
from atomic_agents import AtomicAgent, AgentConfig, BasicChatInputSchema, BasicChatOutputSchema
from atomic_agents.context import SystemPromptGenerator

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
client = instructor.from_openai(openai.OpenAI(api_key=API_KEY))

# System prompt generator setup
system_prompt_generator = SystemPromptGenerator(
    background=["You are a math genius."],
    steps=["Think logically step by step and solve a math problem."],
    output_instructions=["Answer in plain English plus formulas."],
)
# Agent setup with specified configuration
agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](
    config=AgentConfig(
        client=client,
        model="o3-mini",
        system_prompt_generator=system_prompt_generator,
        # It is a convention to use "developer" as the system role for reasoning models from OpenAI such as o1, o3-mini.
        # Also these models are often used without a system prompt, which you can do by setting system_role=None
        system_role="developer",
    )
)

# Prompt the user for input with a styled prompt
user_input = "Decompose this number to prime factors: 1234567890"
console.print(Text("User:", style="bold green"), end=" ")
console.print(user_input)

# Process the user's input through the agent and get the response
input_schema = BasicChatInputSchema(chat_message=user_input)
response = agent.run(input_schema)

agent_message = Text(response.chat_message, style="bold green")
console.print(Text("Agent:", style="bold green"), end=" ")
console.print(agent_message)
