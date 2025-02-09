# Agents

## Schema Hierarchy

The Atomic Agents framework uses Pydantic for schema validation and serialization. All input and output schemas follow this inheritance pattern:

```
pydantic.BaseModel
    └── BaseIOSchema
        ├── BaseAgentInputSchema
        └── BaseAgentOutputSchema
```

### BaseIOSchema

The base schema class that all agent input/output schemas inherit from.

```{eval-rst}
.. py:class:: BaseIOSchema

    Base schema class for all agent input/output schemas. Inherits from :class:`pydantic.BaseModel`.

    All agent schemas must inherit from this class to ensure proper serialization and validation.

    **Inheritance:**
        - :class:`pydantic.BaseModel`
```

### BaseAgentInputSchema

The default input schema for agents.

```{eval-rst}
.. py:class:: BaseAgentInputSchema

    Default input schema for agent interactions.

    **Inheritance:**
        - :class:`BaseIOSchema` → :class:`pydantic.BaseModel`

    .. py:attribute:: chat_message
        :type: str

        The message to send to the agent.

    Example:
        >>> input_schema = BaseAgentInputSchema(chat_message="Hello, agent!")
        >>> agent.run(input_schema)
```

### BaseAgentOutputSchema

The default output schema for agents.

```{eval-rst}
.. py:class:: BaseAgentOutputSchema

    Default output schema for agent responses.

    **Inheritance:**
        - :class:`BaseIOSchema` → :class:`pydantic.BaseModel`

    .. py:attribute:: chat_message
        :type: str

        The response message from the agent.

    Example:
        >>> response = agent.run(input_schema)
        >>> print(response.chat_message)
```

### Creating Custom Schemas

You can create custom input/output schemas by inheriting from `BaseIOSchema`:

```python
from pydantic import Field
from typing import List
from atomic_agents.lib.base.base_io_schema import BaseIOSchema

class CustomInputSchema(BaseIOSchema):
    chat_message: str = Field(..., description="User's message")
    context: str = Field(None, description="Optional context for the agent")

class CustomOutputSchema(BaseIOSchema):
    chat_message: str = Field(..., description="Agent's response")
    follow_up_questions: List[str] = Field(
        default_factory=list,
        description="Suggested follow-up questions"
    )
    confidence: float = Field(
        ...,
        description="Confidence score for the response",
        ge=0.0,
        le=1.0
    )
```

## Base Agent Configuration

### BaseAgentConfig

The configuration class for BaseAgent that defines all settings and components.

```{eval-rst}
.. py:class:: BaseAgentConfig

    Configuration class for BaseAgent.

    **Inheritance:**
        - :class:`pydantic.BaseModel`

    .. py:attribute:: client
        :type: Any

        The LLM client to use (e.g., OpenAI, Anthropic, etc.). Must be wrapped with instructor.

    .. py:attribute:: model
        :type: str

        The model identifier to use with the client (e.g., "gpt-4", "claude-3-opus-20240229").

    .. py:attribute:: memory
        :type: Optional[AgentMemory]

        Memory component for storing conversation history. Defaults to None.

    .. py:attribute:: system_prompt_generator
        :type: Optional[SystemPromptGenerator]

        Generator for creating system prompts. Defaults to None.

    .. py:attribute:: input_schema
        :type: Optional[Type[BaseIOSchema]]

        Schema for validating agent inputs. Defaults to BaseAgentInputSchema.
        Must be a subclass of BaseIOSchema.

    .. py:attribute:: output_schema
        :type: Optional[Type[BaseIOSchema]]

        Schema for validating agent outputs. Defaults to BaseAgentOutputSchema.
        Must be a subclass of BaseIOSchema.

    .. py:attribute:: tools
        :type: Optional[List[str]]

        List of tool names to make available to the agent. Defaults to None.

    .. py:attribute:: tool_configs
        :type: Optional[Dict[str, Dict[str, Any]]]

        Configuration parameters for tools. Defaults to None.

    .. py:attribute:: components
        :type: Optional[Dict[str, Any]]

        Additional components to attach to the agent. Defaults to None.

    Example:
        >>> config = BaseAgentConfig(
        ...     client=instructor.from_openai(OpenAI()),
        ...     model="gpt-4",
        ...     input_schema=CustomInputSchema,
        ...     output_schema=CustomOutputSchema,
        ...     memory=AgentMemory(),
        ...     system_prompt_generator=SystemPromptGenerator(
        ...         background=["You are a helpful assistant"],
        ...         steps=["1. Understand the request", "2. Provide a response"]
        ...     )
        ... )
```

## Base Agent

The BaseAgent class provides core functionality for building AI agents with structured input/output schemas,
memory management, and streaming capabilities.

### Basic Usage

```python
import instructor
from openai import OpenAI
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.components.agent_memory import AgentMemory

# Initialize with OpenAI
client = instructor.from_openai(OpenAI())

# Create basic configuration
config = BaseAgentConfig(
    client=client,
    model="gpt-4",
    memory=AgentMemory()
)

# Initialize agent
agent = BaseAgent(config)
```

### Class Documentation

```{eval-rst}
.. py:class:: BaseAgent

    .. py:method:: __init__(config: BaseAgentConfig)

        Initializes a new BaseAgent instance.

        :param config: Configuration object containing client, model, memory, and other settings
        :type config: BaseAgentConfig

    .. py:method:: run(user_input: Optional[BaseIOSchema] = None) -> BaseIOSchema

        Runs the chat agent with the given user input synchronously.

        :param user_input: The input from the user
        :type user_input: Optional[BaseIOSchema]
        :return: The response from the chat agent
        :rtype: BaseIOSchema

    .. py:method:: run_async(user_input: Optional[BaseIOSchema] = None) -> AsyncGenerator[BaseIOSchema, None]

        Runs the chat agent with streaming output asynchronously.

        :param user_input: The input from the user
        :type user_input: Optional[BaseIOSchema]
        :return: An async generator yielding partial responses
        :rtype: AsyncGenerator[BaseIOSchema, None]

    .. py:method:: reset_memory()

        Resets the agent's memory to its initial state.

    .. py:method:: get_context_provider(provider_name: str) -> Type[SystemPromptContextProviderBase]

        Retrieves a context provider by name.

        :param provider_name: The name of the context provider
        :type provider_name: str
        :return: The context provider if found
        :rtype: SystemPromptContextProviderBase
        :raises KeyError: If the context provider is not found

    .. py:method:: register_context_provider(provider_name: str, provider: SystemPromptContextProviderBase)

        Registers a new context provider.

        :param provider_name: The name of the context provider
        :type provider_name: str
        :param provider: The context provider instance
        :type provider: SystemPromptContextProviderBase

    .. py:method:: unregister_context_provider(provider_name: str)

        Unregisters an existing context provider.

        :param provider_name: The name of the context provider to remove
        :type provider_name: str
        :raises KeyError: If the context provider is not found
```

### Examples

#### Basic Synchronous Interaction

```python
# Create input and get response
user_input = agent.input_schema(chat_message="Tell me about quantum computing")
response = agent.run(user_input)

print(f"Assistant: {response.chat_message}")
```

#### Streaming Response

```python
import asyncio

async def stream_chat():
    # Initialize with AsyncOpenAI for streaming
    client = instructor.from_openai(AsyncOpenAI())
    agent = BaseAgent(BaseAgentConfig(client=client, model="gpt-4"))

    # Create input and stream response
    user_input = agent.input_schema(chat_message="Explain streaming")
    print("\nUser: Explain streaming")
    print("Assistant: ", end="", flush=True)

    async for partial_response in agent.run_async(user_input):
        if hasattr(partial_response, "chat_message"):
            print(partial_response.chat_message, end="", flush=True)
    print()

asyncio.run(stream_chat())
```

#### Using Tools

```python
# Create agent with tools
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4",
        tools=["calculator", "searxng_search"],
        tool_configs={
            "searxng_search": {
                "instance_url": "https://your-searxng-instance.com"
            }
        }
    )
)

# The agent can now use these tools in its responses
response = agent.run(
    agent.input_schema(
        chat_message="What is the square root of 144 plus the current temperature in London?"
    )
)
```

#### Custom Memory and System Prompt

```python
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator

# Create custom system prompt
generator = SystemPromptGenerator(
    background=["You are a helpful AI assistant specializing in technical support."],
    steps=[
        "1. Understand the technical issue",
        "2. Ask clarifying questions if needed",
        "3. Provide step-by-step solutions"
    ]
)

# Create agent with custom memory and prompt
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4",
        memory=AgentMemory(),
        system_prompt_generator=generator
    )
)
```
