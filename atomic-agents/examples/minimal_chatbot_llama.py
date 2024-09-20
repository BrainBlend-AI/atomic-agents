from rich.console import Console
import llama_cpp

# `BaseAgent` is the core class for creating chat agents in the Atomic Agents framework.
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig

# Create an instance of `BaseAgent` with LLaMA settings.
# Ensure you have the LLaMA model path correctly set.
llama_model_path = "./models/7B"  # Update this path to your LLaMA model location
agent = BaseAgent(config=BaseAgentConfig(client=llama_cpp.Llama(model_path=llama_model_path), model="llama-7B"))

# Initialize a `Console` object for rich text output in the terminal.
console = Console()

# Main chat loop for testing the chat agent.
while True:
    user_input = input("You: ")
    if user_input.lower() in ["/exit", "/quit"]:
        print("Exiting chat...")
        break

    response = agent.run(agent.input_schema(chat_message=user_input))
    console.print(f"Agent: {response.chat_message}")
    
#! Make sure you have the llama-cpp-python package installed and the model files available at the specified path.
#! You can refer to the llama-cpp-python documentation for more details on setup and usage. https://llama-cpp-python.readthedocs.io/en/latest/