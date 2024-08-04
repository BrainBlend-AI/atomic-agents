import os
from rich.console import Console
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator
import instructor
import openai

# Define system prompt information including background, steps, and output instructions
system_prompt_generator = SystemPromptGenerator(
    background=[
        "This assistant is a general-purpose AI designed to be helpful and friendly.",
    ],
    steps=["Understand the user's input and provide a relevant response.", "Respond to the user."],
    output_instructions=[
        "Provide helpful and relevant information to assist the user.",
        "Be friendly and respectful in all interactions.",
        "Always answer in rhyming verse.",
    ],
)

# Initialize chat memory to store conversation history
memory = AgentMemory()
# Define initial memory with a greeting message from the assistant
initial_memory = [
    {"role": "assistant", "content": "How do you do? What can I do for you? Tell me, pray, what is your need today?"}
]
# Load the initial memory into the chat memory
memory.load(initial_memory)

# Create a chat agent with the specified model, system prompt generator, and memory
# For all supported clients such as Anthropic & Gemini, have a look at the `instructor` library documentation.

base_url = None  # Replace with your OpenAI API base URL
api_key = None  # Replace with your OpenAI API key
agent = BaseAgent(
    config=BaseAgentConfig(
        client=instructor.from_openai(
            openai.OpenAI(base_url=base_url or os.getenv("OPENAI_BASE_URL"), api_key=api_key or os.getenv("OPENAI_API_KEY"))
        ),
        system_prompt_generator=system_prompt_generator,
        model="gpt-4o-mini",
        memory=memory,
    )
)

# Main chat loop for testing the chat agent
console = Console()
console.print(f'Agent: {initial_memory[0]["content"]}')

while True:
    user_input = input("You: ")
    if user_input.lower() in ["/exit", "/quit"]:
        print("Exiting chat...")
        break

    response = agent.run(agent.input_schema(chat_message=user_input))
    console.print(f"Agent: {response.chat_message}")
