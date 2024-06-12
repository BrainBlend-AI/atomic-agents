# BaseChatAgent

[Atomic_agents Index](../../README.md#atomic_agents-index) / [Atomic Agents](../index.md#atomic-agents) / [Agents](./index.md#agents) / BaseChatAgent

> Auto-generated documentation for [atomic_agents.agents.base_chat_agent](../../../../atomic_agents/agents/base_chat_agent.py) module.

- [BaseChatAgent](#basechatagent)
  - [BaseAgentIO](#baseagentio)
    - [BaseAgentIO().stringify](#baseagentio()stringify)
  - [BaseChatAgent](#basechatagent-1)
    - [BaseChatAgent()._get_and_handle_response](#basechatagent()_get_and_handle_response)
    - [BaseChatAgent()._init_run](#basechatagent()_init_run)
    - [BaseChatAgent()._post_run](#basechatagent()_post_run)
    - [BaseChatAgent()._pre_run](#basechatagent()_pre_run)
    - [BaseChatAgent().get_response](#basechatagent()get_response)
    - [BaseChatAgent().get_system_prompt](#basechatagent()get_system_prompt)
    - [BaseChatAgent().reset_memory](#basechatagent()reset_memory)
    - [BaseChatAgent().run](#basechatagent()run)
  - [BaseChatAgentConfig](#basechatagentconfig)
  - [BaseChatAgentInputSchema](#basechatagentinputschema)
    - [BaseChatAgentInputSchema().stringify](#basechatagentinputschema()stringify)
  - [BaseChatAgentResponse](#basechatagentresponse)
    - [BaseChatAgentResponse().stringify](#basechatagentresponse()stringify)

## BaseAgentIO

[Show source in base_chat_agent.py:8](../../../../atomic_agents/agents/base_chat_agent.py#L8)

Base class for input and output schemas for chat agents.

#### Signature

```python
class BaseAgentIO(BaseModel): ...
```

### BaseAgentIO().stringify

[Show source in base_chat_agent.py:12](../../../../atomic_agents/agents/base_chat_agent.py#L12)

#### Signature

```python
def stringify(self): ...
```



## BaseChatAgent

[Show source in base_chat_agent.py:46](../../../../atomic_agents/agents/base_chat_agent.py#L46)

Base class for chat agents.

This class provides the core functionality for handling chat interactions, including managing memory,
generating system prompts, and obtaining responses from a language model.

#### Attributes

- `input_schema` *Type[BaseAgentIO]* - Schema for the input data.
- `output_schema` *Type[BaseAgentIO]* - Schema for the output data.
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
        config: BaseChatAgentConfig = BaseChatAgentConfig(
            client=instructor.from_openai(openai.OpenAI())
        ),
    ): ...
```

#### See also

- [BaseChatAgentConfig](#basechatagentconfig)

### BaseChatAgent()._get_and_handle_response

[Show source in base_chat_agent.py:131](../../../../atomic_agents/agents/base_chat_agent.py#L131)

Handles obtaining and processing the response.

#### Returns

- `Type[BaseModel]` - The processed response.

#### Signature

```python
def _get_and_handle_response(self): ...
```

### BaseChatAgent()._init_run

[Show source in base_chat_agent.py:141](../../../../atomic_agents/agents/base_chat_agent.py#L141)

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

[Show source in base_chat_agent.py:156](../../../../atomic_agents/agents/base_chat_agent.py#L156)

Finalizes the run with the given response.

#### Arguments

- `response` *Type[BaseModel]* - The response from the chat agent.

#### Signature

```python
def _post_run(self, response): ...
```

### BaseChatAgent()._pre_run

[Show source in base_chat_agent.py:150](../../../../atomic_agents/agents/base_chat_agent.py#L150)

Prepares for the run. This method can be overridden by subclasses to add custom pre-run logic.

#### Signature

```python
def _pre_run(self): ...
```

### BaseChatAgent().get_response

[Show source in base_chat_agent.py:93](../../../../atomic_agents/agents/base_chat_agent.py#L93)

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

[Show source in base_chat_agent.py:84](../../../../atomic_agents/agents/base_chat_agent.py#L84)

Generates the system prompt.

#### Returns

- `str` - The generated system prompt.

#### Signature

```python
def get_system_prompt(self) -> str: ...
```

### BaseChatAgent().reset_memory

[Show source in base_chat_agent.py:78](../../../../atomic_agents/agents/base_chat_agent.py#L78)

Resets the memory to its initial state.

#### Signature

```python
def reset_memory(self): ...
```

### BaseChatAgent().run

[Show source in base_chat_agent.py:114](../../../../atomic_agents/agents/base_chat_agent.py#L114)

Runs the chat agent with the given user input.

#### Arguments

- `user_input` *Optional[str]* - The input text from the user. If not provided, skips the initialization step.

#### Returns

- `str` - The response from the chat agent.

#### Signature

```python
def run(self, user_input: Optional[Type[BaseAgentIO]] = None) -> str: ...
```

#### See also

- [BaseAgentIO](#baseagentio)



## BaseChatAgentConfig

[Show source in base_chat_agent.py:36](../../../../atomic_agents/agents/base_chat_agent.py#L36)

#### Signature

```python
class BaseChatAgentConfig(BaseModel): ...
```



## BaseChatAgentInputSchema

[Show source in base_chat_agent.py:16](../../../../atomic_agents/agents/base_chat_agent.py#L16)

#### Signature

```python
class BaseChatAgentInputSchema(BaseAgentIO): ...
```

#### See also

- [BaseAgentIO](#baseagentio)

### BaseChatAgentInputSchema().stringify

[Show source in base_chat_agent.py:19](../../../../atomic_agents/agents/base_chat_agent.py#L19)

#### Signature

```python
def stringify(self): ...
```



## BaseChatAgentResponse

[Show source in base_chat_agent.py:22](../../../../atomic_agents/agents/base_chat_agent.py#L22)

#### Signature

```python
class BaseChatAgentResponse(BaseAgentIO): ...
```

#### See also

- [BaseAgentIO](#baseagentio)

### BaseChatAgentResponse().stringify

[Show source in base_chat_agent.py:33](../../../../atomic_agents/agents/base_chat_agent.py#L33)

#### Signature

```python
def stringify(self): ...
```