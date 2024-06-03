from datetime import datetime
from rich.console import Console
from atomic_agents.lib.chat_memory import ChatMemory
from atomic_agents_new.agents.basic_chat_agent import BasicChatAgent
from atomic_agents_new.lib.system_prompt_generator import DynamicInfoProviderBase, SystemPrompt
import instructor
import openai
from atomic_agents.tools.searx import SearxNGSearchTool
from atomic_agents.lib.utils.logger import logger

class MyChatAgent(BasicChatAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_tool = SearxNGSearchTool(max_results=15)
    
    def _pre_run(self):
        self.memory.add_message('assistant', 'First, I will perform a search with 3 different search queries to gather relevant information on the topic.')
        search_input = self.get_response(response_model=SearxNGSearchTool.input_schema)
        logger.verbose(f'Search input: {search_input}')
        search_results = self.search_tool.run(search_input)
        self.system_prompt_generator.dynamic_info_providers['search'].search_results = search_results
        self.memory.add_message('assistant', 'I have gathered the search results and they have been added to the context.')
        
class CurrentDateProvider(DynamicInfoProviderBase):
    def __init__(self, title: str, format: str = '%Y-%m-%d %H:%M:%S'):
        super().__init__(title)
        self.format = format

    def get_info(self) -> str:
        return f'The current date, in the format "{self.format}", is {datetime.now().strftime(self.format)}'

class SearchResultsProvider(DynamicInfoProviderBase):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_results: SearxNGSearchTool.output_schema = None

    def get_info(self) -> str:
        response = ''
        if not self.search_results:
            return response
        
        for result in self.search_results.results:
            response += f'--- {result.title} ---\n'
            response += f'{result.content}\n'
            response += f'[Read more]({result.url})\n'
            response += '--------------------------------\n\n'
            
        return response

# Define dynamic info providers
dynamic_info_providers = {
    'date': CurrentDateProvider('Current date', format='%Y-%m-%d %H:%M:%S'),
    'search': SearchResultsProvider('Search results')
}

console = Console()   

system_prompt = SystemPrompt(
    background=[
        'This assistant is an expert in brainstorming ideas and creating article outlines.',
        'This assistant\'s goal is to generate engaging and creative ideas and structured outlines for articles based on the given topic.'
    ],
    steps=[
        'Note the observations about the input and thought process involved in preparing the ideas and outline.',
        'Respond with a list of 10 ideas and a structured outline for the article in a markdown-formatted text.'
    ],
    output_instructions=[
        'Ensure each idea is clearly numbered from 1 to 10.',
        'Output the list of ideas and the article outline in human-readable Markdown format.',
        'Do not include any additional text or confirmation messages; only provide the list of ideas and the article outline.',
        'Do not reply to the user\'s input with anything except the list of ideas and the article outline.'
    ]
)

memory = ChatMemory()
initial_memory = [
    {'role': 'assistant', 'content': 'Hello! I\'m an AI assistant that can help you brainstorm ideas and generate article outlines. Please provide me with a topic to get started.'}
]
memory.load_from_dict_list(initial_memory)        

agent = MyChatAgent(
    client=instructor.from_openai(openai.OpenAI()), 
    model='gpt-3.5-turbo',
    system_prompt=system_prompt,
    memory=memory,
    dynamic_info_providers=dynamic_info_providers
)
console.print(f'Agent: {initial_memory[0]["content"]}')

while True:
    user_input = input('You: ')
    if user_input.lower() in ['exit', 'quit']:
        print('Exiting chat...')
        break

    response = agent.run(user_input)
    console.print(f'Agent: {response.response}')