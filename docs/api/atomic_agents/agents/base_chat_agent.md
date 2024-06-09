# BaseChatAgent

[Atomic_agents Index](../../README.md#atomic_agents-index) / [Atomic Agents](../index.md#atomic-agents) / [Agents](./index.md#agents) / BaseChatAgent

> Auto-generated documentation for [atomic_agents.agents.base_chat_agent](../../../../atomic_agents/agents/base_chat_agent.py) module.

- [BaseChatAgent](#basechatagent)
  - [BaseChatAgent](#basechatagent-1)
    - [BaseChatAgent()._get_and_handle_response](#basechatagent()_get_and_handle_response)
    - [BaseChatAgent()._init_run](#basechatagent()_init_run)
    - [BaseChatAgent()._post_run](#basechatagent()_post_run)
    - [BaseChatAgent()._pre_run](#basechatagent()_pre_run)
    - [BaseChatAgent().get_response](#basechatagent()get_response)
    - [BaseChatAgent().get_system_prompt](#basechatagent()get_system_prompt)
    - [BaseChatAgent().reset_memory](#basechatagent()reset_memory)
    - [BaseChatAgent().run](#basechatagent()run)
  - [BaseChatAgentInputSchema](#basechatagentinputschema)
  - [BaseChatAgentResponse](#basechatagentresponse)

## BaseChatAgent

[Show source in base_chat_agent.py:21](../../../../atomic_agents/agents/base_chat_agent.py#L21)

Base class for chat agents.

This class provides the core functionality for handling chat interactions, including managing memory,
generating system prompts, and obtaining responses from a language model.

#### Attributes

- `input_schema` *Type[BaseModel]* - Schema for the input data.
- `output_schema` *Type[BaseModel]* - Schema for the output data.
- `client` - Client for interacting with the language model.
- `model` *str* - The model to use for generating responses.
- `memory` *ChatMemory* - Memory component for storing chat history.
- `system_prompt_generator` *SystemPromptGenerator* - Component for generating system prompts.
- `initial_memory` *ChatMemory* - Initial state of the memory.

#### Signature

```python
class BaseChatAgent:
    def __init__(
        self,
        client,
        system_prompt_generator: SystemPromptGenerator = None,
        model: str = "gpt-3.5-turbo",
        memory: ChatMemory = None,
        include_planning_step=False,
        input_schema=BaseChatAgentInputSchema,
        output_schema=BaseChatAgentResponse,
    ): ...
```

#### See also

- [BaseChatAgentInputSchema](#basechatagentinputschema)
- [BaseChatAgentResponse](#basechatagentresponse)
- [ChatMemory](../lib/components/chat_memory.md#chatmemory)
- [SystemPromptGenerator](../lib/components/system_prompt_generator.md#systempromptgenerator)

### BaseChatAgent()._get_and_handle_response

[Show source in base_chat_agent.py:111](../../../../atomic_agents/agents/base_chat_agent.py#L111)

Handles obtaining and processing the response.

#### Returns

- `Type[BaseModel]` - The processed response.

#### Signature

```python
def _get_and_handle_response(self): ...
```

### BaseChatAgent()._init_run

[Show source in base_chat_agent.py:121](../../../../atomic_agents/agents/base_chat_agent.py#L121)

Initializes the run with the given user input.

#### Arguments

- `user_input` *str* - The input text from the user.

#### Signature

```python
def _init_run(self, user_input): ...
```

### BaseChatAgent()._post_run

[Show source in base_chat_agent.py:136](../../../../atomic_agents/agents/base_chat_agent.py#L136)

Finalizes the run with the given response.

#### Arguments

- `response` *Type[BaseModel]* - The response from the chat agent.

#### Signature

```python
def _post_run(self, response): ...
```

### BaseChatAgent()._pre_run

[Show source in base_chat_agent.py:130](../../../../atomic_agents/agents/base_chat_agent.py#L130)

Prepares for the run. This method can be overridden by subclasses to add custom pre-run logic.

#### Signature

```python
def _pre_run(self): ...
```

### BaseChatAgent().get_response

[Show source in base_chat_agent.py:73](../../../../atomic_agents/agents/base_chat_agent.py#L73)

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

[Show source in base_chat_agent.py:64](../../../../atomic_agents/agents/base_chat_agent.py#L64)

Generates the system prompt.

#### Returns

- `str` - The generated system prompt.

#### Signature

```python
def get_system_prompt(self) -> str: ...
```

### BaseChatAgent().reset_memory

[Show source in base_chat_agent.py:58](../../../../atomic_agents/agents/base_chat_agent.py#L58)

Resets the memory to its initial state.

#### Signature

```python
def reset_memory(self): ...
```

### BaseChatAgent().run

[Show source in base_chat_agent.py:94](../../../../atomic_agents/agents/base_chat_agent.py#L94)

Runs the chat agent with the given user input.

#### Arguments

- `user_input` *Optional[str]* - The input text from the user. If not provided, skips the initialization step.

#### Returns

- `str` - The response from the chat agent.

#### Signature

```python
def run(self, user_input: Optional[str] = None) -> str: ...
```



## BaseChatAgentInputSchema

[Show source in base_chat_agent.py:7](../../../../atomic_agents/agents/base_chat_agent.py#L7)

#### Signature

```python
class BaseChatAgentInputSchema(BaseModel): ...
```



## BaseChatAgentResponse

[Show source in base_chat_agent.py:10](../../../../atomic_agents/agents/base_chat_agent.py#L10)

#### Signature

```python
class BaseChatAgentResponse(BaseModel): ...
```