from datetime import datetime
from rich.console import Console
from atomic_agents.lib.components.chat_memory import ChatMemory
from atomic_agents.agents.base_chat_agent import BaseChatAgent
from atomic_agents.lib.components.system_prompt_generator import DynamicInfoProviderBase, SystemPromptGenerator, SystemPromptInfo
import instructor
import openai

console = Console()

class CurrentDateProvider(DynamicInfoProviderBase):
    def __init__(self, title: str, format: str = '%Y-%m-%d %H:%M:%S'):
        super().__init__(title)
        self.format = format

    def get_info(self) -> str:
        return f'The current date, in the format "{self.format}", is {datetime.now().strftime(self.format)}'

dynamic_info_providers = {
    'date': CurrentDateProvider('Current date', format='%Y-%m-%d'),
}

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
        'Always answer in rhyming verse. Preferably in alexandrine verse.'
    ]
)
system_prompt_generator = SystemPromptGenerator(system_prompt, dynamic_info_providers)

memory = ChatMemory()
initial_memory = [
    {'role': 'assistant', 'content': 'How do you do? What can I do for you? Tell me, pray, what is your need today?'}
]

memory.load(initial_memory)        

agent = BaseChatAgent(
    client=instructor.from_openai(openai.OpenAI()), 
    system_prompt_generator=system_prompt_generator,
    model='gpt-3.5-turbo',
    memory=memory,
)
console.print(f'Agent: {initial_memory[0]["content"]}')

while True:
    user_input = input('You: ')
    if user_input.lower() in ['exit', 'quit']:
        print('Exiting chat...')
        break

    response = agent.run(user_input)
    console.print(f'Agent: {response.response}')