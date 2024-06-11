from typing import List, Optional, Type
import instructor
import openai
from pydantic import BaseModel, Field
from atomic_agents.lib.components.chat_memory import ChatMemory
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

class BaseChatAgentConfig(BaseModel):
    client: instructor.client.Instructor = Field(..., description='Client for interacting with the language model.')
    model: str = Field("gpt-3.5-turbo", description='The model to use for generating responses.')
    memory: Optional[ChatMemory] = Field(None, description='Memory component for storing chat history.')
    system_prompt_generator: Optional[SystemPromptGenerator] = Field(None, description='Component for generating system prompts.')
    input_schema: Type[BaseModel] = Field(BaseChatAgentInputSchema, description='Schema for the input data.')
    output_schema: Type[BaseModel] = Field(BaseChatAgentResponse, description='Schema for the output data.')
    
    class Config:
        arbitrary_types_allowed = True

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
        initial_memory (ChatMemory): Initial state of the memory.
    """

    def __init__(self, config: BaseChatAgentConfig = BaseChatAgentConfig(client=instructor.from_openai(openai.OpenAI()))):
        """
        Initializes the BaseChatAgent.

        Args:
            config (BaseChatAgentConfig): Configuration for the chat agent.
        """
        self.input_schema = config.input_schema
        self.output_schema = config.output_schema
        self.client = config.client
        self.model = config.model
        self.memory = config.memory or ChatMemory()
        self.system_prompt_generator = config.system_prompt_generator or SystemPromptGenerator()
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