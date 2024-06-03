import os
from typing import Callable, List
from pydantic import BaseModel, Field
from datetime import datetime
from groq import Groq
import instructor
import openai
from atomic_agents.lib.chat_memory import ChatMemory
from rich.console import Console

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

class DynamicInfoProvider:
    def __init__(self, provider_func: Callable[..., str], title: str, *args, **kwargs):
        self.provider_func = provider_func
        self.title = title
        self.args = args
        self.kwargs = kwargs

    def get_info(self) -> str:
        return self.provider_func(*self.args, **self.kwargs)

class SystemPromptGenerator:
    def __init__(self, system_prompt: SystemPrompt, dynamic_info_providers: List[DynamicInfoProvider] = None):
        self.system_prompt = system_prompt
        self.dynamic_info_providers = dynamic_info_providers or []

    def generate_prompt(self) -> str:
        # Generate the prompt
        system_prompt = ''

        if self.system_prompt.background:
            system_prompt += '# IDENTITY and PURPOSE\n'
            system_prompt += f'-{'\n-'.join(self.system_prompt.background)}\n\n'

        if self.system_prompt.steps:
            system_prompt += '# Steps\n'
            system_prompt += f'-{'\n-'.join(self.system_prompt.steps)}\n\n'

        if self.system_prompt.output_instructions:
            system_prompt += '# OUTPUT INSTRUCTIONS\n'
            system_prompt += f'-{'\n-'.join(self.system_prompt.output_instructions)}\n\n'

        if self.dynamic_info_providers:
            system_prompt += '# EXTRA INFORMATION AND CONTEXT\n'
            for provider in self.dynamic_info_providers:
                system_prompt += f'## {provider.title}\n'
                system_prompt += f'{provider.get_info()}\n\n'

        return system_prompt

class BasicChatAgent:
    def __init__(self, client, model: str = 'gpt-3.5-turbo', system_prompt: SystemPrompt = None, memory: ChatMemory = None, vector_db = None, input_schema = BasicChatAgentInputSchema, output_schema = BasicChatAgentResponse, dynamic_info_providers: List[DynamicInfoProvider] = None):
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
        self.prompt_generator = SystemPromptGenerator(self.system_prompt, dynamic_info_providers)

    def get_system_prompt(self) -> str:
        return self.prompt_generator.generate_prompt()

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
        response = self.get_response(response_model=self.output_schema)
        self.memory.add_message('assistant', response.model_dump_json())
        return response

if __name__ == '__main__':   
    console = Console()
    
    openai_client = openai.OpenAI()
    client = instructor.from_openai(openai_client)
    model = 'gpt-3.5-turbo'
    groq_client = instructor.from_groq(Groq(api_key=os.getenv('GROQ_API_KEY')))
    groq_model = os.getenv('GROQ_CHAT_MODEL')
    
    class MyChatAgentResponse(BaseModel):
        observations: List[str] = Field(..., description='What the agent observes in the current state of the conversation.')
        thought_process: List[str] = Field(..., description='The thought process of the agent in formulating the response.')
        final_response: str = Field(..., description='The markdown-enabled response from the chat agent.')
        
        class Config:
            title = 'BasicChatAgentResponse'
            description = 'Response from the basic chat agent. The response can be in markdown format.'
            json_schema_extra = {
                'title': title,
                'description': description
            }

    system_prompt = SystemPrompt(
        background=[
            'You are an expert in creating viral video ideas.',
            'Your goal is to generate engaging and creative video concepts that have the potential to go viral on social media platforms.'
        ],
        steps=[
            'Take the input given as the topic for the video ideas.',
            'Brainstorm and create a list of 10 unique and creative video ideas based on the given topic.',
            'Ensure that each idea is designed to capture attention and encourage sharing.'
        ],
        output_instructions=[
            'Ensure each idea is clearly numbered from 1 to 10.',
            'Output the list in human-readable Markdown format.',
            'Do not include any additional text or confirmation messages; only provide the list of 10 viral video ideas.'
        ]
    )

    
    memory = ChatMemory()
    initial_memory = [
        {'role': 'assistant', 'content': 'Hello! I\'m an AI assistant that can help you generate viral video ideas. Please provide me with a topic to get started.'}
    ]
    memory.load_from_dict_list(initial_memory)

    # Define dynamic info providers
    def current_date_provider(format: str = '%Y-%m-%dT%H:%M:%S') -> str:
        return f'The current date, in the format "{format}", is {datetime.now().strftime(format)}'

    dynamic_info_providers = [DynamicInfoProvider(current_date_provider, 'Current date', format='%Y-%m-%d %H:%M:%S')]

    agent = BasicChatAgent(
        client=client, 
        model=model, 
        system_prompt=system_prompt,
        memory=memory,
        dynamic_info_providers=dynamic_info_providers,
        output_schema=MyChatAgentResponse
    )
    console.print(f'Agent: {initial_memory[0]["content"]}')

    while True:
        user_input = input('You: ')
        if user_input.lower() in ['exit', 'quit']:
            print('Exiting chat...')
            break

        response = agent.run(user_input)
        console.print(f'Agent: {response.final_response}')