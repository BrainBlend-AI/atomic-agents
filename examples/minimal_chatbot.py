from rich.console import Console
import instructor
import openai

# `BaseChatAgent` is the core class for creating chat agents in the Atomic Agents framework.
from atomic_agents.agents.base_chat_agent import BaseChatAgent

# Create an instance of `BaseChatAgent` with default settings.
# The `from_openai` function wraps the OpenAI client to work seamlessly with the Atomic Agents framework.
# `openai.OpenAI()` creates a client instance for the OpenAI API.
# The `model` parameter specifies the language model to use, in this case, 'gpt-3.5-turbo'.
agent = BaseChatAgent(
    client=instructor.from_openai(openai.OpenAI()), 
    model='gpt-3.5-turbo',
)

# Initialize a `Console` object for rich text output in the terminal.
console = Console()

# Start an infinite loop to keep the chatbot running until the user decides to exit.
while True:
    # Prompt the user for input.
    user_input = input('You: ')
    # Check if the user wants to exit the chat.
    if user_input.lower() in ['/exit', '/quit']:
        print('Exiting chat...')
        break

    # Process the user input through the chat agent to get a response.
    response = agent.run(user_input)
    # Use the `console` object to print the agent's response in a rich format.
    console.print(f'Agent: {response.response}')