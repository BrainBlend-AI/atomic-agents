from typing import List
from pydantic import BaseModel, Field
from atomic_agents.lib.components.chat_memory import ChatMemory
from atomic_agents.lib.utils.logger import logger
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

# Input and Response Schemas
class BaseChatAgentInputSchema(BaseModel):
    chat_input: str = Field(..., description='The input text for the chat agent.')

class BaseChatAgentResponse(BaseModel):    
    response: str = Field(..., description='The markdown-enabled response from the chat agent.')
    
    class Config:
        title = 'BaseChatAgentResponse'
        description = 'Response from the base chat agent. The response can be in markdown format. This response is the only thing the user will see in the chat interface.'
        json_schema_extra = {
            'title': title,
            'description': description
        }

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

# Base Chat Agent Class
class BaseChatAgent:
    def __init__(self, client, system_prompt_generator: SystemPromptGenerator = None, model: str = 'gpt-3.5-turbo',  memory: ChatMemory = None, include_planning_step = False, input_schema = BaseChatAgentInputSchema, output_schema = BaseChatAgentResponse):
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.client = client
        self.model = model
        self.memory = memory or ChatMemory()
        self.system_prompt_generator = system_prompt_generator or SystemPromptGenerator()
        self.include_planning_step = include_planning_step
        self.initial_memory = self.memory.copy()
        
    def reset_memory(self):
        self.memory = self.initial_memory.copy()
        
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
        self._init_run(user_input)
        self._pre_run()
        if self.include_planning_step:
            self._plan_run()
        response = self._get_and_handle_response()
        self._post_run(response)
        return response
    
    def _get_and_handle_response(self):
        return self.get_response(response_model=self.output_schema)

    def _plan_run(self):
        self.memory.add_message('assistant', 'I will now note any observations about the relevant input, context and thought process involved in preparing the response.')
        plan = self.get_response(response_model=GeneralPlanResponse)
        self.memory.add_message('assistant', plan.model_dump_json())

    def _init_run(self, user_input):
        self.memory.add_message('user', user_input)

    def _pre_run(self):
        pass
    
    def _post_run(self, response):
        self.memory.add_message('assistant', response.model_dump_json())