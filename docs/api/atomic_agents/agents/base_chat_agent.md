# BaseChatAgent

[Atomic_agents Index](../../README.md#atomic_agents-index) / [Atomic Agents](../index.md#atomic-agents) / [Agents](./index.md#agents) / BaseChatAgent

> Auto-generated documentation for [atomic_agents.agents.base_chat_agent](../../../../atomic_agents/agents/base_chat_agent.py) module.

- [BaseChatAgent](#basechatagent)
  - [BaseAgentIO](#baseagentio)
  - [BaseChatAgent](#basechatagent-1)
    - [BaseChatAgent()._get_and_handle_response](#basechatagent()_get_and_handle_response)
    - [BaseChatAgent()._init_run](#basechatagent()_init_run)
    - [BaseChatAgent()._post_run](#basechatagent()_post_run)
    - [BaseChatAgent()._pre_run](#basechatagent()_pre_run)
    - [BaseChatAgent().get_context_provider](#basechatagent()get_context_provider)
    - [BaseChatAgent().get_response](#basechatagent()get_response)
    - [BaseChatAgent().get_system_prompt](#basechatagent()get_system_prompt)
    - [BaseChatAgent().register_context_provider](#basechatagent()register_context_provider)
    - [BaseChatAgent().reset_memory](#basechatagent()reset_memory)
    - [BaseChatAgent().run](#basechatagent()run)
    - [BaseChatAgent().unregister_context_provider](#basechatagent()unregister_context_provider)
  - [BaseChatAgentConfig](#basechatagentconfig)
  - [BaseChatAgentInputSchema](#basechatagentinputschema)
  - [BaseChatAgentOutputSchema](#basechatagentoutputschema)

## BaseAgentIO

[Show source in base_chat_agent.py:10](../../../../atomic_agents/agents/base_chat_agent.py#L10)

Base class for input and output schemas for chat agents.

#### Signature

```python
class BaseAgentIO(BaseModel): ...
```



## BaseChatAgent

[Show source in base_chat_agent.py:62](../../../../atomic_agents/agents/base_chat_agent.py#L62)

Base class for chat agents.

This class provides the core functionality for handling chat interactions, including managing memory,
generating system prompts, and obtaining responses from a language model.

#### Attributes

- `input_schema` *Type[BaseAgentIO]* - Schema for the input data.
- `output_schema` *Type[BaseAgentIO]* - Schema for the output data.
- `client` - Client for interacting with the language model.
- `model` *str* - The model to use for generating responses.
- `memory` *AgentMemory* - Memory component for storing chat history.
- `system_prompt_generator` *SystemPromptGenerator* - Component for generating system prompts.
- `initial_memory` *AgentMemory* - Initial state of the memory.

#### Signature

```python
class BaseChatAgent:
    def __init__(
        self,
        config: BaseChatAgentConfig = BaseChatAgentConfig(
            client=instructor.from_openai(openai.OpenAI())
        ),
    ): ...
```

#### See also

- [BaseChatAgentConfig](#basechatagentconfig)

### BaseChatAgent()._get_and_handle_response

[Show source in base_chat_agent.py:150](../../../../atomic_agents/agents/base_chat_agent.py#L150)

Handles obtaining and processing the response.

#### Returns

- `Type[BaseModel]` - The processed response.

#### Signature

```python
def _get_and_handle_response(self): ...
```

### BaseChatAgent()._init_run

[Show source in base_chat_agent.py:159](../../../../atomic_agents/agents/base_chat_agent.py#L159)

Initializes the run with the given user input.

#### Arguments

- `user_input` *str* - The input text from the user.

#### Signature

```python
def _init_run(self, user_input: Type[BaseAgentIO]): ...
```

#### See also

- [BaseAgentIO](#baseagentio)

### BaseChatAgent()._post_run

[Show source in base_chat_agent.py:175](../../../../atomic_agents/agents/base_chat_agent.py#L175)

Finalizes the run with the given response.

#### Arguments

- `response` *Type[BaseModel]* - The response from the chat agent.

#### Signature

```python
def _post_run(self, response): ...
```

### BaseChatAgent()._pre_run

[Show source in base_chat_agent.py:169](../../../../atomic_agents/agents/base_chat_agent.py#L169)

Prepares for the run. This method can be overridden by subclasses to add custom pre-run logic.

#### Signature

```python
def _pre_run(self): ...
```

### BaseChatAgent().get_context_provider

[Show source in base_chat_agent.py:184](../../../../atomic_agents/agents/base_chat_agent.py#L184)

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

### BaseChatAgent().get_response

[Show source in base_chat_agent.py:112](../../../../atomic_agents/agents/base_chat_agent.py#L112)

Obtains a response from the language model.

#### Arguments

- `response_model` *Type[BaseModel], optional* - The schema for the response data. If not set, self.output_schema is used.

#### Returns

- `Type[BaseModel]` - The response from the language model.

#### Signature

```python
def get_response(self, response_model=None) -> Type[BaseModel]: ...
```

### BaseChatAgent().get_system_prompt

[Show source in base_chat_agent.py:103](../../../../atomic_agents/agents/base_chat_agent.py#L103)

Generates the system prompt.

#### Returns

- `str` - The generated system prompt.

#### Signature

```python
def get_system_prompt(self) -> str: ...
```

### BaseChatAgent().register_context_provider

[Show source in base_chat_agent.py:201](../../../../atomic_agents/agents/base_chat_agent.py#L201)

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

### BaseChatAgent().reset_memory

[Show source in base_chat_agent.py:97](../../../../atomic_agents/agents/base_chat_agent.py#L97)

Resets the memory to its initial state.

#### Signature

```python
def reset_memory(self): ...
```

### BaseChatAgent().run

[Show source in base_chat_agent.py:133](../../../../atomic_agents/agents/base_chat_agent.py#L133)

Runs the chat agent with the given user input.

#### Arguments

- `user_input` *Optional[str]* - The input text from the user. If not provided, skips the initialization step.

#### Returns

- `str` - The response from the chat agent.

#### Signature

```python
def run(self, user_input: Optional[Type[BaseAgentIO]] = None) -> Type[BaseAgentIO]: ...
```

#### See also

- [BaseAgentIO](#baseagentio)

### BaseChatAgent().unregister_context_provider

[Show source in base_chat_agent.py:211](../../../../atomic_agents/agents/base_chat_agent.py#L211)

Unregisters an existing context provider.

#### Arguments

- `provider_name` *str* - The name of the context provider to remove.

#### Signature

```python
def unregister_context_provider(self, provider_name: str): ...
```



## BaseChatAgentConfig

[Show source in base_chat_agent.py:51](../../../../atomic_agents/agents/base_chat_agent.py#L51)

#### Signature

```python
class BaseChatAgentConfig(BaseModel): ...
```



## BaseChatAgentInputSchema

[Show source in base_chat_agent.py:21](../../../../atomic_agents/agents/base_chat_agent.py#L21)

#### Signature

```python
class BaseChatAgentInputSchema(BaseAgentIO): ...
```

#### See also

- [BaseAgentIO](#baseagentio)



## BaseChatAgentOutputSchema

[Show source in base_chat_agent.py:36](../../../../atomic_agents/agents/base_chat_agent.py#L36)

#### Signature

```python
class BaseChatAgentOutputSchema(BaseAgentIO): ...
```

#### See also

- [BaseAgentIO](#baseagentio)