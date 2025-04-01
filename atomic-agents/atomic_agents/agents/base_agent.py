import instructor
from pydantic import BaseModel, Field
from typing import Optional, Type
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.lib.components.system_prompt_generator import (
    SystemPromptContextProviderBase,
    SystemPromptGenerator,
)
from atomic_agents.lib.base.base_io_schema import BaseIOSchema

from instructor.dsl.partial import PartialBase
from jiter import from_json
import warnings


def model_from_chunks_patched(cls, json_chunks, **kwargs):
    potential_object = ""
    partial_model = cls.get_partial_model()
    for chunk in json_chunks:
        potential_object += chunk
        obj = from_json((potential_object or "{}").encode(), partial_mode="trailing-strings")
        obj = partial_model.model_validate(obj, strict=None, **kwargs)
        yield obj


async def model_from_chunks_async_patched(cls, json_chunks, **kwargs):
    potential_object = ""
    partial_model = cls.get_partial_model()
    async for chunk in json_chunks:
        potential_object += chunk
        obj = from_json((potential_object or "{}").encode(), partial_mode="trailing-strings")
        obj = partial_model.model_validate(obj, strict=None, **kwargs)
        yield obj


PartialBase.model_from_chunks = classmethod(model_from_chunks_patched)
PartialBase.model_from_chunks_async = classmethod(model_from_chunks_async_patched)


class BaseAgentInputSchema(BaseIOSchema):
    """This schema represents the input from the user to the AI agent."""

    chat_message: str = Field(
        ...,
        description="The chat message sent by the user to the assistant.",
    )


class BaseAgentOutputSchema(BaseIOSchema):
    """This schema represents the response generated by the chat agent."""

    chat_message: str = Field(
        ...,
        description=(
            "The chat message exchanged between the user and the chat agent. "
            "This contains the markdown-enabled response generated by the chat agent."
        ),
    )


class BaseAgentConfig(BaseModel):
    client: instructor.client.Instructor = Field(..., description="Client for interacting with the language model.")
    model: str = Field("gpt-4o-mini", description="The model to use for generating responses.")
    memory: Optional[AgentMemory] = Field(None, description="Memory component for storing chat history.")
    system_prompt_generator: Optional[SystemPromptGenerator] = Field(
        None, description="Component for generating system prompts."
    )
    system_role: Optional[str] = Field(
        "system", description="The role of the system in the conversation. None means no system prompt."
    )
    input_schema: Optional[Type[BaseModel]] = Field(None, description="The schema for the input data.")
    output_schema: Optional[Type[BaseModel]] = Field(None, description="The schema for the output data.")
    model_config = {"arbitrary_types_allowed": True}
    temperature: Optional[float] = Field(
        None,
        description="Temperature for response generation, typically ranging from 0 to 1.",
    )
    max_tokens: Optional[int] = Field(
        None,
        description="Maximum number of token allowed in the response generation.",
    )
    model_api_parameters: Optional[dict] = Field(None, description="Additional parameters passed to the API provider.")


class BaseAgent:
    """
    Base class for chat agents.

    This class provides the core functionality for handling chat interactions, including managing memory,
    generating system prompts, and obtaining responses from a language model.

    Attributes:
        input_schema (Type[BaseIOSchema]): Schema for the input data.
        output_schema (Type[BaseIOSchema]): Schema for the output data.
        client: Client for interacting with the language model.
        model (str): The model to use for generating responses.
        memory (AgentMemory): Memory component for storing chat history.
        system_prompt_generator (SystemPromptGenerator): Component for generating system prompts.
        initial_memory (AgentMemory): Initial state of the memory.
        temperature (float): Temperature for response generation, typically ranging from 0 to 1.  For models such as
            OpenAI o3-mini that do not support temperature, you must explicitly pass 'None'.
            DEPRECATED: Include 'temperature' in model_api_parameters instead.
        max_tokens (int): Maximum number of tokens allowed in the response.
            DEPRECATED: Include 'max_tokens' in model_api_parameters instead.
        model_api_parameters (dict): Additional parameters passed to the API provider.
    """

    input_schema = BaseAgentInputSchema
    output_schema = BaseAgentOutputSchema

    def __init__(self, config: BaseAgentConfig):
        """
        Initializes the BaseAgent.

        Args:
            config (BaseAgentConfig): Configuration for the chat agent.
        """
        self.input_schema = config.input_schema or self.input_schema
        self.output_schema = config.output_schema or self.output_schema
        self.client = config.client
        self.model = config.model
        self.memory = config.memory or AgentMemory()
        self.system_prompt_generator = config.system_prompt_generator or SystemPromptGenerator()
        self.system_role = config.system_role
        self.initial_memory = self.memory.copy()
        self.current_user_input = None
        self.model_api_parameters = config.model_api_parameters or {}
        if config.temperature is not None:
            warnings.warn(
                "'temperature' is deprecated and will soon be removed. Please use 'model_api_parameters' instead.",
                DeprecationWarning,
            )
            if "temperature" not in self.model_api_parameters:
                self.model_api_parameters["temperature"] = config.temperature
        if config.max_tokens is not None:
            warnings.warn(
                "'max_tokens' is deprecated and will soon be removed. Please use 'model_api_parameters' instead.",
                DeprecationWarning,
            )
            self.model_api_parameters["max_tokens"] = config.max_tokens

    def reset_memory(self):
        """
        Resets the memory to its initial state.
        """
        self.memory = self.initial_memory.copy()

    def get_response(self, response_model=None) -> Type[BaseModel]:
        """
        Obtains a response from the language model synchronously.

        Args:
            response_model (Type[BaseModel], optional):
                The schema for the response data. If not set, self.output_schema is used.

        Returns:
            Type[BaseModel]: The response from the language model.
        """
        if response_model is None:
            response_model = self.output_schema

        if self.system_role is None:
            self.messages = []
        else:
            self.messages = [
                {
                    "role": self.system_role,
                    "content": self.system_prompt_generator.generate_prompt(),
                }
            ]

        self.messages += self.memory.get_history()

        response = self.client.chat.completions.create(
            messages=self.messages,
            model=self.model,
            response_model=response_model,
            **self.model_api_parameters,
        )

        return response

    def run(self, user_input: Optional[BaseIOSchema] = None) -> BaseIOSchema:
        """
        Runs the chat agent with the given user input synchronously.

        Args:
            user_input (Optional[BaseIOSchema]): The input from the user. If not provided, skips adding to memory.

        Returns:
            BaseIOSchema: The response from the chat agent.
        """
        if user_input:
            self.memory.initialize_turn()
            self.current_user_input = user_input
            self.memory.add_message("user", user_input)

        response = self.get_response(response_model=self.output_schema)
        self.memory.add_message("assistant", response)

        return response

    async def run_async(self, user_input: Optional[BaseIOSchema] = None):
        """
        Runs the chat agent with the given user input, supporting streaming output asynchronously.

        Args:
            user_input (Optional[BaseIOSchema]): The input from the user. If not provided, skips adding to memory.

        Yields:
            BaseModel: Partial responses from the chat agent.
        """
        if user_input:
            self.memory.initialize_turn()
            self.current_user_input = user_input
            self.memory.add_message("user", user_input)

        if self.system_role is None:
            self.messages = []
        else:
            self.messages = [
                {
                    "role": self.system_role,
                    "content": self.system_prompt_generator.generate_prompt(),
                }
            ]

        self.messages += self.memory.get_history()

        response_stream = self.client.chat.completions.create_partial(
            model=self.model,
            messages=self.messages,
            response_model=self.output_schema,
            **self.model_api_parameters,
            stream=True,
        )

        async for partial_response in response_stream:
            yield partial_response

        full_response_content = self.output_schema(**partial_response.model_dump())
        self.memory.add_message("assistant", full_response_content)

    async def run_async_batch(self, user_input: Optional[BaseIOSchema] = None) -> BaseIOSchema:
        """
        Runs the chat agent with the given user input, supporting streaming output asynchronously.

        Args:
            user_input (Optional[BaseIOSchema]): The input from the user. If not provided, skips adding to memory.

        Returns:
            BaseIOSchema: Partial responses from the chat agent.
        """
        if user_input:
            self.memory.initialize_turn()
            self.current_user_input = user_input
            self.memory.add_message("user", user_input)

        if self.system_role is None:
            self.messages = []
        else:
            self.messages = [
                {
                    "role": self.system_role,
                    "content": self.system_prompt_generator.generate_prompt(),
                }
            ]

        self.messages += self.memory.get_history()

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            response_model=self.output_schema,
            **self.model_api_parameters
        )

        self.memory.add_message("assistant", response)
        return response
    async def stream_response_async(self, user_input: Optional[Type[BaseIOSchema]] = None):
        """
        Deprecated method for streaming responses asynchronously. Use run_async instead.

        Args:
            user_input (Optional[Type[BaseIOSchema]]): The input from the user. If not provided, skips adding to memory.

        Yields:
            BaseModel: Partial responses from the chat agent.
        """
        warnings.warn(
            "stream_response_async is deprecated and will be removed in version 1.1. Use run_async instead which can be used in the exact same way.",
            DeprecationWarning,
            stacklevel=2,
        )
        async for response in self.run_async(user_input):
            yield response

    def get_context_provider(self, provider_name: str) -> Type[SystemPromptContextProviderBase]:
        """
        Retrieves a context provider by name.

        Args:
            provider_name (str): The name of the context provider.

        Returns:
            SystemPromptContextProviderBase: The context provider if found.

        Raises:
            KeyError: If the context provider is not found.
        """
        if provider_name not in self.system_prompt_generator.context_providers:
            raise KeyError(f"Context provider '{provider_name}' not found.")
        return self.system_prompt_generator.context_providers[provider_name]

    def register_context_provider(self, provider_name: str, provider: SystemPromptContextProviderBase):
        """
        Registers a new context provider.

        Args:
            provider_name (str): The name of the context provider.
            provider (SystemPromptContextProviderBase): The context provider instance.
        """
        self.system_prompt_generator.context_providers[provider_name] = provider

    def unregister_context_provider(self, provider_name: str):
        """
        Unregisters an existing context provider.

        Args:
            provider_name (str): The name of the context provider to remove.
        """
        if provider_name in self.system_prompt_generator.context_providers:
            del self.system_prompt_generator.context_providers[provider_name]
        else:
            raise KeyError(f"Context provider '{provider_name}' not found.")


if __name__ == "__main__":
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.syntax import Syntax
    from rich import box
    from openai import OpenAI, AsyncOpenAI
    import instructor
    import asyncio
    from rich.live import Live
    import json

    def _create_schema_table(title: str, schema: Type[BaseModel]) -> Table:
        """Create a table displaying schema information.

        Args:
            title (str): Title of the table
            schema (Type[BaseModel]): Schema to display

        Returns:
            Table: Rich table containing schema information
        """
        schema_table = Table(title=title, box=box.ROUNDED)
        schema_table.add_column("Field", style="cyan")
        schema_table.add_column("Type", style="magenta")
        schema_table.add_column("Description", style="green")

        for field_name, field in schema.model_fields.items():
            schema_table.add_row(field_name, str(field.annotation), field.description or "")

        return schema_table

    def _create_config_table(agent: BaseAgent) -> Table:
        """Create a table displaying agent configuration.

        Args:
            agent (BaseAgent): Agent instance

        Returns:
            Table: Rich table containing configuration information
        """
        info_table = Table(title="Agent Configuration", box=box.ROUNDED)
        info_table.add_column("Property", style="cyan")
        info_table.add_column("Value", style="yellow")

        info_table.add_row("Model", agent.model)
        info_table.add_row("Memory", str(type(agent.memory).__name__))
        info_table.add_row("System Prompt Generator", str(type(agent.system_prompt_generator).__name__))

        return info_table

    def display_agent_info(agent: BaseAgent):
        """Display information about the agent's configuration and schemas."""
        console = Console()
        console.print(
            Panel.fit(
                "[bold blue]Agent Information[/bold blue]",
                border_style="blue",
                padding=(1, 1),
            )
        )

        # Display input schema
        input_schema_table = _create_schema_table("Input Schema", agent.input_schema)
        console.print(input_schema_table)

        # Display output schema
        output_schema_table = _create_schema_table("Output Schema", agent.output_schema)
        console.print(output_schema_table)

        # Display configuration
        info_table = _create_config_table(agent)
        console.print(info_table)

        # Display system prompt
        system_prompt = agent.system_prompt_generator.generate_prompt()
        console.print(
            Panel(
                Syntax(system_prompt, "markdown", theme="monokai", line_numbers=True),
                title="Sample System Prompt",
                border_style="green",
                expand=False,
            )
        )

    async def chat_loop(streaming: bool = False):
        """Interactive chat loop with the AI agent.

        Args:
            streaming (bool): Whether to use streaming mode for responses
        """
        if streaming:
            client = instructor.from_openai(AsyncOpenAI())
            config = BaseAgentConfig(client=client, model="gpt-4o-mini")
            agent = BaseAgent(config)
        else:
            client = instructor.from_openai(OpenAI())
            config = BaseAgentConfig(client=client, model="gpt-4o-mini")
            agent = BaseAgent(config)

        # Display agent information before starting the chat
        display_agent_info(agent)

        console = Console()
        console.print(
            Panel.fit(
                "[bold blue]Interactive Chat Mode[/bold blue]\n"
                f"[cyan]Streaming: {streaming}[/cyan]\n"
                "Type 'exit' to quit",
                border_style="blue",
                padding=(1, 1),
            )
        )

        while True:
            user_message = console.input("\n[bold green]You:[/bold green] ")

            if user_message.lower() == "exit":
                console.print("[yellow]Goodbye![/yellow]")
                break

            user_input = agent.input_schema(chat_message=user_message)

            console.print("[bold blue]Assistant:[/bold blue]")
            if streaming:
                with Live(console=console, refresh_per_second=4) as live:
                    async for partial_response in agent.run_async(user_input):
                        response_json = partial_response.model_dump()
                        json_str = json.dumps(response_json, indent=2)
                        live.update(json_str)
            else:
                response = agent.run(user_input)
                response_json = response.model_dump()
                json_str = json.dumps(response_json, indent=2)
                console.print(json_str)

    console = Console()
    console.print("\n[bold]Starting chat loop...[/bold]")
    asyncio.run(chat_loop(streaming=True))
