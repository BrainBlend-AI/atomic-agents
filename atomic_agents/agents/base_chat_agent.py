from typing import List, Optional, Type
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

class BaseChatAgent:
    """
    Base class for chat agents.

    This class provides the core functionality for handling chat interactions, including managing memory,
    generating system prompts, and obtaining responses from a language model.

    Attributes:
        input_schema (Type[BaseModel]): Schema for the input data.
        output_schema (Type[BaseModel]): Schema for the output data.
        client: Client for interacting with the language model.
        model (str): The model to use for generating responses.
        memory (ChatMemory): Memory component for storing chat history.
        system_prompt_generator (SystemPromptGenerator): Component for generating system prompts.
        include_planning_step (bool): Whether to include a planning step in the response generation.
        initial_memory (ChatMemory): Initial state of the memory.
    """

    def __init__(self, client, system_prompt_generator: SystemPromptGenerator = None, model: str = 'gpt-3.5-turbo', memory: ChatMemory = None, include_planning_step=False, input_schema=BaseChatAgentInputSchema, output_schema=BaseChatAgentResponse):
        """
        Initializes the BaseChatAgent.

        Args:
            client: Client for interacting with the language model.
            system_prompt_generator (SystemPromptGenerator, optional): Component for generating system prompts. Defaults to None.
            model (str, optional): The model to use for generating responses. Defaults to 'gpt-3.5-turbo'.
            memory (ChatMemory, optional): Memory component for storing chat history. Defaults to None.
            include_planning_step (bool, optional): Whether to include a planning step in the response generation. Defaults to False.
            input_schema (Type[BaseModel], optional): Schema for the input data. Defaults to BaseChatAgentInputSchema.
            output_schema (Type[BaseModel], optional): Schema for the output data. Defaults to BaseChatAgentResponse.
        """
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.client = client
        self.model = model
        self.memory = memory or ChatMemory()
        self.system_prompt_generator = system_prompt_generator or SystemPromptGenerator()
        self.include_planning_step = include_planning_step
        self.initial_memory = self.memory.copy()

    def reset_memory(self):
        """
        Resets the memory to its initial state.
        """
        self.memory = self.initial_memory.copy()

    def get_system_prompt(self) -> str:
        """
        Generates the system prompt.

        Returns:
            str: The generated system prompt.
        """
        return self.system_prompt_generator.generate_prompt()

    def get_response(self, response_model=None) -> Type[BaseModel]:
        """
        Obtains a response from the language model.

        Args:
            response_model (Type[BaseModel], optional): The schema for the response data. If not set, self.output_schema is used.

        Returns:
            Type[BaseModel]: The response from the language model.
        """
        if response_model is None:
            response_model = self.output_schema

        messages = [{'role': 'system', 'content': self.get_system_prompt()}] + self.memory.get_history()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_model=response_model
        )
        return response

    def run(self, user_input: Optional[str] = None) -> str:
        """
        Runs the chat agent with the given user input.

        Args:
            user_input (Optional[str]): The input text from the user. If not provided, skips the initialization step.

        Returns:
            str: The response from the chat agent.
        """
        if user_input:
            self._init_run(user_input)
        self._pre_run()
        if self.include_planning_step:
            self._plan_run()
        response = self._get_and_handle_response()
        self._post_run(response)
        return response

    def _get_and_handle_response(self):
        """
        Handles obtaining and processing the response.

        Returns:
            Type[BaseModel]: The processed response.
        """
        return self.get_response(response_model=self.output_schema)

    def _plan_run(self):
        """
        Executes the planning step, if included.
        """
        self.memory.add_message('assistant', 'I will now note any observations about the relevant input, context and thought process involved in preparing the response.')
        plan = self.get_response(response_model=GeneralPlanResponse)
        self.memory.add_message('assistant', plan.model_dump_json())

    def _init_run(self, user_input):
        """
        Initializes the run with the given user input.

        Args:
            user_input (str): The input text from the user.
        """
        self.memory.add_message('user', user_input)

    def _pre_run(self):
        """
        Prepares for the run. This method can be overridden by subclasses to add custom pre-run logic.
        """
        pass

    def _post_run(self, response):
        """
        Finalizes the run with the given response.

        Args:
            response (Type[BaseModel]): The response from the chat agent.
        """
        self.memory.add_message('assistant', response.model_dump_json())