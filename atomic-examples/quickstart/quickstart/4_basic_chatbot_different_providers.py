import os
import instructor
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseAgentOutputSchema
from dotenv import load_dotenv

load_dotenv()

# Initialize a Rich Console for pretty console outputs
console = Console()

# Memory setup
memory = AgentMemory()

# Initialize memory with an initial message from the assistant
initial_message = BaseAgentOutputSchema(chat_message="Hello! How can I assist you today?")
memory.add_message("assistant", initial_message)


# Function to set up the client based on the chosen provider
def setup_client(provider):
    if provider == "openai":
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        client = instructor.from_openai(OpenAI(api_key=api_key))
        model = "gpt-4o-mini"
    elif provider == "groq":
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        client = instructor.from_groq(Groq(api_key=api_key), mode=instructor.Mode.JSON)
        model = "mixtral-8x7b-32768"
    elif provider == "ollama":
        from openai import OpenAI as OllamaClient

        client = instructor.from_openai(OllamaClient(base_url="http://localhost:11434/v1", api_key="ollama"))
        model = "llama3"
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return client, model


# Prompt the user to choose a provider
provider = console.input("[bold yellow]Choose a provider (openai/groq/ollama): [/bold yellow]").lower()

# Set up the client and model based on the chosen provider
client, model = setup_client(provider)

# Agent setup with specified configuration
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model=model,
        memory=memory,
    )
)

# Generate the default system prompt for the agent
default_system_prompt = agent.system_prompt_generator.generate_prompt()
# Display the system prompt in a styled panel
console.print(Panel(default_system_prompt, width=console.width, style="bold cyan"), style="bold cyan")

# Display the initial message from the assistant
console.print(Text("Agent:", style="bold green"), end=" ")
console.print(Text(initial_message.chat_message, style="bold green"))

# Start an infinite loop to handle user inputs and agent responses
while True:
    # Prompt the user for input with a styled prompt
    user_input = console.input("[bold blue]You:[/bold blue] ")
    # Check if the user wants to exit the chat
    if user_input.lower() in ["/exit", "/quit"]:
        console.print("Exiting chat...")
        break

    # Process the user's input through the agent and get the response
    input_schema = BaseAgentInputSchema(chat_message=user_input)
    response = agent.run(input_schema)

    agent_message = Text(response.chat_message, style="bold green")
    console.print(Text("Agent:", style="bold green"), end=" ")
    console.print(agent_message)
