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
  - [BaseChatAgentConfig](#basechatagentconfig)
  - [BaseChatAgentInputSchema](#basechatagentinputschema)
  - [BaseChatAgentResponse](#basechatagentresponse)

## BaseChatAgent

[Show source in base_chat_agent.py:34](../../../../atomic_agents/agents/base_chat_agent.py#L34)

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
        config: BaseChatAgentConfig = BaseChatAgentConfig(
            client=instructor.from_openai(openai.OpenAI())
        ),
    ): ...
```

#### See also

- [BaseChatAgentConfig](#basechatagentconfig)

### BaseChatAgent()._get_and_handle_response

[Show source in base_chat_agent.py:119](../../../../atomic_agents/agents/base_chat_agent.py#L119)

Handles obtaining and processing the response.

#### Returns

- `Type[BaseModel]` - The processed response.

#### Signature

```python
def _get_and_handle_response(self): ...
```

### BaseChatAgent()._init_run

[Show source in base_chat_agent.py:129](../../../../atomic_agents/agents/base_chat_agent.py#L129)

Initializes the run with the given user input.

#### Arguments

- `user_input` *str* - The input text from the user.

#### Signature

```python
def _init_run(self, user_input): ...
```

### BaseChatAgent()._post_run

[Show source in base_chat_agent.py:144](../../../../atomic_agents/agents/base_chat_agent.py#L144)

Finalizes the run with the given response.

#### Arguments

- `response` *Type[BaseModel]* - The response from the chat agent.

#### Signature

```python
def _post_run(self, response): ...
```

### BaseChatAgent()._pre_run

[Show source in base_chat_agent.py:138](../../../../atomic_agents/agents/base_chat_agent.py#L138)

Prepares for the run. This method can be overridden by subclasses to add custom pre-run logic.

#### Signature

```python
def _pre_run(self): ...
```

### BaseChatAgent().get_response

[Show source in base_chat_agent.py:81](../../../../atomic_agents/agents/base_chat_agent.py#L81)

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

[Show source in base_chat_agent.py:72](../../../../atomic_agents/agents/base_chat_agent.py#L72)

Generates the system prompt.

#### Returns

- `str` - The generated system prompt.

#### Signature

```python
def get_system_prompt(self) -> str: ...
```

### BaseChatAgent().reset_memory

[Show source in base_chat_agent.py:66](../../../../atomic_agents/agents/base_chat_agent.py#L66)

Resets the memory to its initial state.

#### Signature

```python
def reset_memory(self): ...
```

### BaseChatAgent().run

[Show source in base_chat_agent.py:102](../../../../atomic_agents/agents/base_chat_agent.py#L102)

Runs the chat agent with the given user input.

#### Arguments

- `user_input` *Optional[str]* - The input text from the user. If not provided, skips the initialization step.

#### Returns

- `str` - The response from the chat agent.

#### Signature

```python
def run(self, user_input: Optional[str] = None) -> str: ...
```



## BaseChatAgentConfig

[Show source in base_chat_agent.py:23](../../../../atomic_agents/agents/base_chat_agent.py#L23)

#### Signature

```python
class BaseChatAgentConfig(BaseModel): ...
```



## BaseChatAgentInputSchema

[Show source in base_chat_agent.py:9](../../../../atomic_agents/agents/base_chat_agent.py#L9)

#### Signature

```python
class BaseChatAgentInputSchema(BaseModel): ...
```



## BaseChatAgentResponse

[Show source in base_chat_agent.py:12](../../../../atomic_agents/agents/base_chat_agent.py#L12)

#### Signature

```python
class BaseChatAgentResponse(BaseModel): ...
```