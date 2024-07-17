# BaseAgent

[Atomic_agents Index](../../README.md#atomic_agents-index) / [Atomic Agents](../index.md#atomic-agents) / [Agents](./index.md#agents) / BaseAgent

> Auto-generated documentation for [atomic_agents.agents.base_agent](../../../../atomic_agents/agents/base_agent.py) module.

- [BaseAgent](#baseagent)
  - [BaseAgent](#baseagent-1)
    - [BaseAgent().get_context_provider](#baseagent()get_context_provider)
    - [BaseAgent().get_response](#baseagent()get_response)
    - [BaseAgent().register_context_provider](#baseagent()register_context_provider)
    - [BaseAgent().reset_memory](#baseagent()reset_memory)
    - [BaseAgent().run](#baseagent()run)
    - [BaseAgent().unregister_context_provider](#baseagent()unregister_context_provider)
  - [BaseAgentConfig](#baseagentconfig)
  - [BaseIOSchema](#baseagentio)
  - [BaseAgentInputSchema](#baseagentinputschema)
  - [BaseAgentOutputSchema](#baseagentoutputschema)

## BaseAgent

[Show source in base_agent.py:71](../../../../atomic_agents/agents/base_agent.py#L71)

Base class for chat agents.

This class provides the core functionality for handling chat interactions, including managing memory,
generating system prompts, and obtaining responses from a language model.

#### Attributes

- `input_schema` *Type[BaseIOSchema]* - Schema for the input data.
- `output_schema` *Type[BaseIOSchema]* - Schema for the output data.
- `client` - Client for interacting with the language model.
- `model` *str* - The model to use for generating responses.
- `memory` *AgentMemory* - Memory component for storing chat history.
- `system_prompt_generator` *SystemPromptGenerator* - Component for generating system prompts.
- `initial_memory` *AgentMemory* - Initial state of the memory.

#### Signature

```python
class BaseAgent:
    def __init__(self, config: BaseAgentConfig): ...
```

#### See also

- [BaseAgentConfig](#baseagentconfig)

### BaseAgent().get_context_provider

[Show source in base_agent.py:155](../../../../atomic_agents/agents/base_agent.py#L155)

Retrieves a context provider by name.

#### Arguments

- `provider_name` *str* - The name of the context provider.

#### Returns

- `SystemPromptContextProviderBase` - The context provider if found.

#### Raises

- `KeyError` - If the context provider is not found.

#### Signature

```python
def get_context_provider(
    self, provider_name: str
) -> Type[SystemPromptContextProviderBase]: ...
```

#### See also

- [SystemPromptContextProviderBase](../lib/components/system_prompt_generator.md#systempromptcontextproviderbase)

### BaseAgent().get_response

[Show source in base_agent.py:113](../../../../atomic_agents/agents/base_agent.py#L113)

Obtains a response from the language model.

#### Arguments

response_model (Type[BaseModel], optional):
    The schema for the response data. If not set, self.output_schema is used.

#### Returns

- `Type[BaseModel]` - The response from the language model.

#### Signature

```python
def get_response(self, response_model=None) -> Type[BaseModel]: ...
```

### BaseAgent().register_context_provider

[Show source in base_agent.py:172](../../../../atomic_agents/agents/base_agent.py#L172)

Registers a new context provider.

#### Arguments

- `provider_name` *str* - The name of the context provider.
- `provider` *SystemPromptContextProviderBase* - The context provider instance.

#### Signature

```python
def register_context_provider(
    self, provider_name: str, provider: SystemPromptContextProviderBase
): ...
```

#### See also

- [SystemPromptContextProviderBase](../lib/components/system_prompt_generator.md#systempromptcontextproviderbase)

### BaseAgent().reset_memory

[Show source in base_agent.py:107](../../../../atomic_agents/agents/base_agent.py#L107)

Resets the memory to its initial state.

#### Signature

```python
def reset_memory(self): ...
```

### BaseAgent().run

[Show source in base_agent.py:136](../../../../atomic_agents/agents/base_agent.py#L136)

Runs the chat agent with the given user input.

#### Arguments

- `user_input` *Optional[Type[BaseIOSchema]]* - The input from the user. If not provided, skips adding to memory.

#### Returns

- `Type[BaseIOSchema]` - The response from the chat agent.

#### Signature

```python
def run(self, user_input: Optional[Type[BaseIOSchema]] = None) -> Type[BaseIOSchema]: ...
```

#### See also

- [BaseIOSchema](#baseagentio)

### BaseAgent().unregister_context_provider

[Show source in base_agent.py:182](../../../../atomic_agents/agents/base_agent.py#L182)

Unregisters an existing context provider.

#### Arguments

- `provider_name` *str* - The name of the context provider to remove.

#### Signature

```python
def unregister_context_provider(self, provider_name: str): ...
```



## BaseAgentConfig

[Show source in base_agent.py:57](../../../../atomic_agents/agents/base_agent.py#L57)

#### Signature

```python
class BaseAgentConfig(BaseModel): ...
```



## BaseIOSchema

[Show source in base_agent.py:11](../../../../atomic_agents/agents/base_agent.py#L11)

Base class for input and output schemas for chat agents.

#### Signature

```python
class BaseIOSchema(BaseModel): ...
```



## BaseAgentInputSchema

[Show source in base_agent.py:24](../../../../atomic_agents/agents/base_agent.py#L24)

#### Signature

```python
class BaseAgentInputSchema(BaseIOSchema): ...
```

#### See also

- [BaseIOSchema](#baseagentio)



## BaseAgentOutputSchema

[Show source in base_agent.py:39](../../../../atomic_agents/agents/base_agent.py#L39)

#### Signature

```python
class BaseAgentOutputSchema(BaseIOSchema): ...
```

#### See also

- [BaseIOSchema](#baseagentio)