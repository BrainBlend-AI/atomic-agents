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

console = Console()

# Memory setup
memory = AgentMemory()
initial_memory = [
    {"role": "assistant", "content": "How do you do? What can I do for you? Tell me, pray, what is your need today?"}
]
memory.load(initial_memory)

# OpenAI client setup
client = instructor.from_openai(openai.OpenAI(api_key=API_KEY))

# Agent setup
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        memory=memory,
    )
)

agent_message = Text(initial_memory[0]["content"], style="bold green")
console.print(Text("Agent:", style="bold green"), end=" ")
console.print(agent_message)

while True:
    user_input = console.input("[bold blue]You:[/bold blue] ")
    if user_input.lower() in ["/exit", "/quit"]:
        console.print("Exiting chat...")
        break

    response = agent.run(agent.input_schema(chat_message=user_input))
    agent_message = Text(response.chat_message, style="bold green")
    console.print(Text("Agent:", style="bold green"), end=" ")
    console.print(agent_message)
