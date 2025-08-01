# Agents

## Schema Hierarchy

The Atomic Agents framework uses Pydantic for schema validation and serialization. All input and output schemas follow this inheritance pattern:

```PlainText
pydantic.BaseModel
    └── BaseIOSchema
        ├── BasicChatInputSchema
        └── BasicChatOutputSchema
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

### BasicChatInputSchema

The default input schema for agents.

```{eval-rst}
.. py:class:: BasicChatInputSchema

    Default input schema for agent interactions.

    **Inheritance:**
        - :class:`BaseIOSchema` → :class:`pydantic.BaseModel`

    .. py:attribute:: chat_message
        :type: str

        The message to send to the agent.

    Example:
        >>> input_schema = BasicChatInputSchema(chat_message="Hello, agent!")
        >>> agent.run(input_schema)
```

### BasicChatOutputSchema

The default output schema for agents.

```{eval-rst}
.. py:class:: BasicChatOutputSchema

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
from atomic_agents import BaseIOSchema

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

## Base Agent

The `AtomicAgent` class is the foundation for building AI agents in the Atomic Agents framework. It handles chat interactions, history management, system prompts, and responses from language models.

```python
from atomic_agents import AtomicAgent, AgentConfig
from atomic_agents.context import ChatHistory, SystemPromptGenerator

# Create agent with basic configuration
agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](
    config=AgentConfig(
        client=instructor.from_openai(OpenAI()),
        model="gpt-4-turbo-preview",
        history=ChatHistory(),
        system_prompt_generator=SystemPromptGenerator()
    )
)

# Run the agent
response = agent.run(user_input)

# Stream responses
async for partial_response in agent.run_async(user_input):
    print(partial_response)
```

### Configuration

The `AgentConfig` class provides configuration options:

```python
class AgentConfig:
    client: instructor.Instructor  # Client for interacting with the language model
    model: str = "gpt-4-turbo-preview"  # Model to use
    history: Optional[ChatHistory] = None  # History component
    system_prompt_generator: Optional[SystemPromptGenerator] = None  # Prompt generator
    input_schema: Optional[Type[BaseModel]] = None  # Custom input schema
    output_schema: Optional[Type[BaseModel]] = None  # Custom output schema
    model_api_parameters: Optional[dict] = None  # Additional API parameters
```

### Input/Output Schemas

Default schemas for basic chat interactions:

```python
class BasicChatInputSchema(BaseIOSchema):
    """Input from the user to the AI agent."""
    chat_message: str = Field(
        ...,
        description="The chat message sent by the user."
    )

class BasicChatOutputSchema(BaseIOSchema):
    """Response generated by the chat agent."""
    chat_message: str = Field(
        ...,
        description="The markdown-enabled response generated by the chat agent."
    )
```

### Key Methods

- `run(user_input: Optional[BaseIOSchema] = None) -> BaseIOSchema`: Process user input and get response
- `run_async(user_input: Optional[BaseIOSchema] = None)`: Stream responses asynchronously
- `get_response(response_model=None) -> Type[BaseModel]`: Get direct model response
- `reset_history()`: Reset history to initial state
- `get_context_provider(provider_name: str)`: Get a registered context provider
- `register_context_provider(provider_name: str, provider: BaseDynamicContextProvider)`: Register a new context provider
- `unregister_context_provider(provider_name: str)`: Remove a context provider

### Context Providers

Context providers can be used to inject dynamic information into the system prompt:

```python
from atomic_agents.context import BaseDynamicContextProvider

class SearchResultsProvider(BaseDynamicContextProvider):
    def __init__(self, title: str):
        super().__init__(title=title)
        self.results = []

    def get_info(self) -> str:
        return "\n\n".join([
            f"Result {idx}:\n{result}"
            for idx, result in enumerate(self.results, 1)
        ])

# Register with agent
agent.register_context_provider(
    "search_results",
    SearchResultsProvider("Search Results")
)
```

### Streaming Support

The agent supports streaming responses for more interactive experiences:

```python
async def chat():
    async for partial_response in agent.run_async(user_input):
        # Handle each chunk of the response
        print(partial_response.chat_message)
```

### History Management

The agent automatically manages conversation history through the `ChatHistory` component:

```python
# Access history
history = agent.history.get_history()

# Reset to initial state
agent.reset_history()

# Save/load history state
serialized = agent.history.dump()
agent.history.load(serialized)
```

### Custom Schemas

You can use custom input/output schemas for structured interactions:

```python
from pydantic import BaseModel, Field
from typing import List

class CustomInput(BaseIOSchema):
    """Custom input with specific fields"""
    question: str = Field(..., description="User's question")
    context: str = Field(..., description="Additional context")

class CustomOutput(BaseIOSchema):
    """Custom output with structured data"""
    answer: str = Field(..., description="Answer to the question")
    sources: List[str] = Field(..., description="Source references")

# Create agent with custom schemas
agent = AtomicAgent[CustomInput, CustomOutput](
    config=AgentConfig(
        client=client,
        model=model,
    )
)
```

For full API details:
```{eval-rst}
.. automodule:: atomic_agents.agents.atomic_agent
   :members:
   :undoc-members:
   :show-inheritance:
```
