from rich.console import Console
from atomic_agents.agents.base_chat_agent import BaseChatAgent
import instructor
import openai

console = Console()

agent = BaseChatAgent(
    client=instructor.from_openai(openai.OpenAI()), 
    model='gpt-3.5-turbo',
)

while True:
    user_input = input('You: ')
    if user_input.lower() in ['exit', 'quit']:
        print('Exiting chat...')
        break

    response = agent.run(user_input)
    console.print(f'Agent: {response.response}')