"""
This example demonstrates how to create a custom chatbot with custom personality using the Atomic Agents library.
"""

from rich.console import Console
from atomic_agents.lib.components.chat_memory import ChatMemory
from atomic_agents.agents.base_chat_agent import BaseChatAgent, BaseChatAgentConfig
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptInfo
import instructor
import openai

# Define system prompt information including background, steps, and output instructions
system_prompt = SystemPromptInfo(
    background=[
        'This assistant is a general-purpose AI designed to be helpful and friendly.',
    ],
    steps=[
        'Understand the user\'s input and provide a relevant response.',
        'Respond to the user.'
    ],
    output_instructions=[
        'Provide helpful and relevant information to assist the user.',
        'Be friendly and respectful in all interactions.',
        'Always answer in rhyming verse.'
    ]
)
# Initialize the system prompt generator with the defined system prompt and dynamic info providers
system_prompt_generator = SystemPromptGenerator(system_prompt)

# Initialize chat memory to store conversation history
memory = ChatMemory()
# Define initial memory with a greeting message from the assistant
initial_memory = [
    {'role': 'assistant', 'content': 'How do you do? What can I do for you? Tell me, pray, what is your need today?'}
]
# Load the initial memory into the chat memory
memory.load(initial_memory)        

# Create a chat agent with the specified model, system prompt generator, and memory
# For all supported clients such as Anthropic & Gemini, have a look at the `instructor` library documentation.
agent = BaseChatAgent(
    config=BaseChatAgentConfig(
        client=instructor.from_openai(openai.OpenAI()), 
        system_prompt_generator=system_prompt_generator,
        model='gpt-3.5-turbo',
        memory=memory,
    )
)

# Main chat loop for testing the chat agent
console = Console()
console.print(f'Agent: {initial_memory[0]["content"]}')

while True:
    user_input = input('You: ')
    if user_input.lower() in ['/exit', '/quit']:
        print('Exiting chat...')
        break

    response = agent.run(user_input)
    console.print(f'Agent: {response.response}')