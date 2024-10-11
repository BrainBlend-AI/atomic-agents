import os
import instructor
import openai
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig

# API Key setup
API_KEY = ""
if not API_KEY:
    API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise ValueError("API key is not set. Please set the API key as a static variable or in the environment variable OPENAI_API_KEY.")

# Initialize a Rich Console for pretty console outputs
console = Console()

# Memory setup
memory = AgentMemory()

# Initialize memory with an initial message from the assistant
initial_memory = [
    {"role": "assistant", "content": "How do you do? What can I do for you? Tell me, pray, what is your need today?"}
]
memory.load(initial_memory)

# OpenAI client setup using the Instructor library
# Note, you can also set up a client using any other LLM provider, such as Anthropic, Cohere, etc.
# See the Instructor library for more information: https://github.com/instructor-ai/instructor
client = instructor.from_openai(openai.OpenAI(api_key=API_KEY))

# Agent setup with specified configuration
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        memory=memory,
    )
)

# Generate the default system prompt for the agent
default_system_prompt = agent.system_prompt_generator.generate_prompt()
# Display the system prompt in a styled panel
console.print(Panel(default_system_prompt, width=console.width, style="bold cyan"), style="bold cyan")

# Display the initial message from the assistant
agent_message = Text(initial_memory[0]["content"], style="bold green")
console.print(Text("Agent:", style="bold green"), end=" ")
console.print(agent_message)

# Start an infinite loop to handle user inputs and agent responses
while True:
    # Prompt the user for input with a styled prompt
    user_input = console.input("[bold blue]You:[/bold blue] ")
    # Check if the user wants to exit the chat
    if user_input.lower() in ["/exit", "/quit"]:
        console.print("Exiting chat...")
        break

    # Process the user's input through the agent and get the response and display it
    response = agent.run(agent.input_schema(chat_message=user_input))
    agent_message = Text(response.chat_message, style="bold green")
    console.print(Text("Agent:", style="bold green"), end=" ")
    console.print(agent_message)
