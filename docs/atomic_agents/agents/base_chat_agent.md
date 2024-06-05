# BaseChatAgent

[Atomic_agents_redux Index](../../README.md#atomic_agents_redux-index) / [Atomic Agents](../index.md#atomic-agents) / [Agents](./index.md#agents) / BaseChatAgent

> Auto-generated documentation for [atomic_agents.agents.base_chat_agent](../../../atomic_agents/agents/base_chat_agent.py) module.

- [BaseChatAgent](#basechatagent)
  - [BaseChatAgent](#basechatagent-1)
    - [BaseChatAgent()._get_and_handle_response](#basechatagent()_get_and_handle_response)
    - [BaseChatAgent()._init_run](#basechatagent()_init_run)
    - [BaseChatAgent()._plan_run](#basechatagent()_plan_run)
    - [BaseChatAgent()._post_run](#basechatagent()_post_run)
    - [BaseChatAgent()._pre_run](#basechatagent()_pre_run)
    - [BaseChatAgent().get_response](#basechatagent()get_response)
    - [BaseChatAgent().get_system_prompt](#basechatagent()get_system_prompt)
    - [BaseChatAgent().reset_memory](#basechatagent()reset_memory)
    - [BaseChatAgent().run](#basechatagent()run)
  - [BaseChatAgentInputSchema](#basechatagentinputschema)
  - [BaseChatAgentResponse](#basechatagentresponse)
  - [GeneralPlanResponse](#generalplanresponse)
  - [GeneralPlanStep](#generalplanstep)

## BaseChatAgent

[Show source in base_chat_agent.py:40](../../../atomic_agents/agents/base_chat_agent.py#L40)

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
- `include_planning_step` *bool* - Whether to include a planning step in the response generation.
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

[Show source in base_chat_agent.py:134](../../../atomic_agents/agents/base_chat_agent.py#L134)

Handles obtaining and processing the response.

#### Returns

- `Type[BaseModel]` - The processed response.

#### Signature

```python
def _get_and_handle_response(self): ...
```

### BaseChatAgent()._init_run

[Show source in base_chat_agent.py:151](../../../atomic_agents/agents/base_chat_agent.py#L151)

Initializes the run with the given user input.

#### Arguments

- `user_input` *str* - The input text from the user.

#### Signature

```python
def _init_run(self, user_input): ...
```

### BaseChatAgent()._plan_run

[Show source in base_chat_agent.py:143](../../../atomic_agents/agents/base_chat_agent.py#L143)

Executes the planning step, if included.

#### Signature

```python
def _plan_run(self): ...
```

### BaseChatAgent()._post_run

[Show source in base_chat_agent.py:166](../../../atomic_agents/agents/base_chat_agent.py#L166)

Finalizes the run with the given response.

#### Arguments

- `response` *Type[BaseModel]* - The response from the chat agent.

#### Signature

```python
def _post_run(self, response): ...
```

### BaseChatAgent()._pre_run

[Show source in base_chat_agent.py:160](../../../atomic_agents/agents/base_chat_agent.py#L160)

Prepares for the run. This method can be overridden by subclasses to add custom pre-run logic.

#### Signature

```python
def _pre_run(self): ...
```

### BaseChatAgent().get_response

[Show source in base_chat_agent.py:95](../../../atomic_agents/agents/base_chat_agent.py#L95)

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

[Show source in base_chat_agent.py:86](../../../atomic_agents/agents/base_chat_agent.py#L86)

Generates the system prompt.

#### Returns

- `str` - The generated system prompt.

#### Signature

```python
def get_system_prompt(self) -> str: ...
```

### BaseChatAgent().reset_memory

[Show source in base_chat_agent.py:80](../../../atomic_agents/agents/base_chat_agent.py#L80)

Resets the memory to its initial state.

#### Signature

```python
def reset_memory(self): ...
```

### BaseChatAgent().run

[Show source in base_chat_agent.py:116](../../../atomic_agents/agents/base_chat_agent.py#L116)

Runs the chat agent with the given user input.

#### Arguments

- `user_input` *str* - The input text from the user.

#### Returns

- `str` - The response from the chat agent.

#### Signature

```python
def run(self, user_input: str) -> str: ...
```



## BaseChatAgentInputSchema

[Show source in base_chat_agent.py:8](../../../atomic_agents/agents/base_chat_agent.py#L8)

#### Signature

```python
class BaseChatAgentInputSchema(BaseModel): ...
```



## BaseChatAgentResponse

[Show source in base_chat_agent.py:11](../../../atomic_agents/agents/base_chat_agent.py#L11)

#### Signature

```python
class BaseChatAgentResponse(BaseModel): ...
```



## GeneralPlanResponse

[Show source in base_chat_agent.py:27](../../../atomic_agents/agents/base_chat_agent.py#L27)

#### Signature

```python
class GeneralPlanResponse(BaseModel): ...
```



## GeneralPlanStep

[Show source in base_chat_agent.py:22](../../../atomic_agents/agents/base_chat_agent.py#L22)

#### Signature

```python
class GeneralPlanStep(BaseModel): ...
```