"""
This example demonstrates how to create a chat agent that generates article ideas and outlines based on a given topic.
The agent uses a search tool to gather relevant information and provides a structured outline for an article based on the search results.
This script also demonstrates the usage of dynamic info providers to include additional dynamic information at runtime in the system prompt context.
This can be useful if you only want to include the latest search results to save tokens (and thus, money) and avoid unnecessary repetition.
"""

from datetime import datetime
from rich.console import Console
from atomic_agents.lib.components.chat_memory import ChatMemory
from atomic_agents.agents.base_chat_agent import BaseChatAgent
from atomic_agents.lib.components.system_prompt_generator import DynamicInfoProviderBase, SystemPromptGenerator, SystemPromptInfo
import instructor
import openai
from atomic_agents.lib.tools.searx import SearxNGSearchTool
from atomic_agents.lib.utils.logger import logger


# For this example, we extend the BaseChatAgent to create a custom chat agent that interacts with a search tool.
class MyChatAgent(BaseChatAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.search_tool = SearxNGSearchTool(max_results=25)
    
    def _pre_run(self):
        self.memory.add_message('assistant', 'First, I will perform a search with 3 different search queries to gather relevant information on the topic.')
        search_input = self.get_response(response_model=SearxNGSearchTool.input_schema)
        logger.verbose(f'Search input: {search_input}')
        search_results = self.search_tool.run(search_input)
        self.system_prompt_generator.dynamic_info_providers['search'].search_results = search_results
        self.memory.add_message('assistant', 'I have gathered the search results and they have been added to the context.')

# We can define dynamic info providers to provide additional information in the system prompt context.
# Each provider must have a title and a `get_info` method that returns a string. 
# Each run, get_info will be called in order to provide the information at runtime.
class CurrentDateProvider(DynamicInfoProviderBase):
    def __init__(self, format: str = '%Y-%m-%d %H:%M:%S', **kwargs):
        super().__init__(**kwargs)
        self.format = format

    def get_info(self) -> str:
        return f'The current date, in the format "{self.format}", is {datetime.now().strftime(self.format)}'

class SearchResultsProvider(DynamicInfoProviderBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
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

# Define dynamic info providers.
dynamic_info_providers = {
    'date': CurrentDateProvider(title='Current date', format='%Y-%m-%d %H:%M:%S'),
    'search': SearchResultsProvider(title='Search results')
}

# Define the system prompt information including background, steps, and output instructions.
system_prompt = SystemPromptInfo(
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
        'Include a list of the most promising-looking URLs for further research at the end of the response as a markdown list.',
        'Do not include any additional text or confirmation messages; only provide the list of ideas, the article outline, and the URLs.',
        'Do not reply to the user\'s input with anything except the list of ideas, the article outline, and the URLs.'
    ]
)
system_prompt_generator = SystemPromptGenerator(system_prompt, dynamic_info_providers)

# Optionally define the memory with an initial message from the assistant.
memory = ChatMemory()
initial_memory = [
    {'role': 'assistant', 'content': 'Hello! I\'m an AI assistant that can help you brainstorm ideas and generate article outlines. Please provide me with a topic to get started.'}
]
memory.load(initial_memory)        

# Create a chat agent with the specified model, system prompt generator, and memory.
# For all supported clients such as Anthropic & Gemini, have a look at the `instructor` library documentation.
agent = MyChatAgent(
    client=instructor.from_openai(openai.OpenAI()), 
    system_prompt_generator=system_prompt_generator,
    model='gpt-3.5-turbo',
    memory=memory,
)

console = Console()

console.print(f'Agent: {initial_memory[0]["content"]}')

while True:
    user_input = input('You: ')
    if user_input.lower() in ['exit', 'quit']:
        print('Exiting chat...')
        break

    response = agent.run(user_input)
    console.print(f'Agent: {response.response}')