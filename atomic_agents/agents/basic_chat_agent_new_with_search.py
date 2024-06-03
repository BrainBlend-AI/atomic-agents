from typing import Callable, List
from pydantic import BaseModel, Field
from datetime import datetime
from abc import ABC, abstractmethod
from atomic_agents.lib.chat_memory import ChatMemory
from atomic_agents.lib.utils.logger import logger

class BasicChatAgentInputSchema(BaseModel):
    chat_input: str = Field(..., description='The input text for the chat agent.')

class BasicChatAgentResponse(BaseModel):    
    response: str = Field(..., description='The markdown-enabled response from the chat agent.')
    
    class Config:
        title = 'BasicChatAgentResponse'
        description = 'Response from the basic chat agent. The response can be in markdown format.'
        json_schema_extra = {
            'title': title,
            'description': description
        }

class SystemPrompt(BaseModel):
    background: List[str]
    steps: List[str]
    output_instructions: List[str]

class DynamicInfoProviderBase(ABC):
    def __init__(self, title: str):
        self.title = title

    @abstractmethod
    def get_info(self) -> str:
        pass
    
class SystemPromptGenerator:
    def __init__(self, system_prompt: SystemPrompt, dynamic_info_providers: dict[str, DynamicInfoProviderBase] = None):
        self.system_prompt = system_prompt
        self.dynamic_info_providers = dynamic_info_providers or {}

    def generate_prompt(self) -> str:
        system_prompt = ''

        if self.system_prompt.background:
            system_prompt += '# IDENTITY and PURPOSE\n'
            system_prompt += f'-{'\n-'.join(self.system_prompt.background)}\n\n'

        if self.system_prompt.steps:
            system_prompt += '# INTERNAL ASSISTANT STEPS\n'
            system_prompt += f'-{'\n-'.join(self.system_prompt.steps)}\n\n'

        if self.system_prompt.output_instructions:
            system_prompt += '# OUTPUT INSTRUCTIONS\n'
            system_prompt += f'-{'\n-'.join(self.system_prompt.output_instructions)}\n\n'

        if self.dynamic_info_providers:
            system_prompt += '# EXTRA INFORMATION AND CONTEXT\n'
            for provider in self.dynamic_info_providers.values():
                info = provider.get_info()
                if info:
                    system_prompt += f'## {provider.title}\n'
                    system_prompt += f'{info}\n\n'

        return system_prompt

class GeneralPlanStep(BaseModel):
    step: str
    description: str
    substeps: List[str] = []

class GeneralPlanResponse(BaseModel):
    observations: List[str] = Field(..., description='Key points or observations about the input.')
    thoughts: List[str] = Field(..., description='Thought process or considerations involved in preparing the response.')
    response_plan: List[GeneralPlanStep] = Field(..., description='Steps involved in generating the response.')

    class Config:
        title = 'GeneralPlanResponse'
        description = 'General response plan from the chat agent.'
        json_schema_extra = {
            'title': title,
            'description': description
        }

class BasicChatAgent:
    def __init__(self, client, model: str = 'gpt-3.5-turbo', system_prompt: SystemPrompt = None, memory: ChatMemory = None, include_planning_step = False, input_schema = BasicChatAgentInputSchema, output_schema = BasicChatAgentResponse, dynamic_info_providers: dict[str, DynamicInfoProviderBase] = None):
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.client = client
        self.model = model
        self.memory = memory or ChatMemory()
        self.system_prompt = system_prompt or SystemPrompt(
            background=['You are a helpful AI assistant.'],
            steps=[],
            output_instructions=[]
        )
        self.system_prompt_generator = SystemPromptGenerator(self.system_prompt, dynamic_info_providers)
        self.include_planning_step = include_planning_step

    def get_system_prompt(self) -> str:
        return self.system_prompt_generator.generate_prompt()

    def get_response(self, response_model=None) -> BaseModel:
        if response_model is None:
            response_model = self.output_schema
        
        messages = [{'role': 'system', 'content': self.get_system_prompt()}] + self.memory.get_history()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_model=response_model
        )
        return response

    def run(self, user_input: str) -> str:
        self.memory.add_message('user', user_input)
        self._pre_run()
        if self.include_planning_step:
            self.memory.add_message('assistant', 'I will now note the observations about the input and context and the thought process involved in preparing the response.')
            plan = self.get_response(response_model=GeneralPlanResponse)
            self.memory.add_message('assistant', plan.model_dump_json())
        response = self.get_response(response_model=self.output_schema)
        self.memory.add_message('assistant', response.model_dump_json())
        self._post_run()
        return response

    def _pre_run(self):
        pass
    
    def _post_run(self):
        pass

if __name__ == '__main__':
    import instructor
    import openai
    from rich.console import Console
    from atomic_agents.tools.searx import SearxNGSearchTool

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