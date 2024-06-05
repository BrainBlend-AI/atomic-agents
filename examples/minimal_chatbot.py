from rich.console import Console
import instructor
import openai

# `BaseChatAgent` is the core class for creating chat agents in the Atomic Agents framework.
from atomic_agents.agents.base_chat_agent import BaseChatAgent

# Create an instance of `BaseChatAgent` with default settings.
# For all supported clients such as Anthropic & Gemini, have a look at the `instructor` library documentation.
agent = BaseChatAgent(
    client=instructor.from_openai(openai.OpenAI()), 
    model='gpt-3.5-turbo',
)

# Initialize a `Console` object for rich text output in the terminal.
console = Console()

# Main chat loop for testing the chat agent.
while True:
    user_input = input('You: ')
    if user_input.lower() in ['/exit', '/quit']:
        print('Exiting chat...')
        break

    response = agent.run(user_input)
    console.print(f'Agent: {response.response}')