# AgentMemory

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Components](./index.md#components) / AgentMemory

> Auto-generated documentation for [atomic_agents.lib.components.agent_memory](../../../../../atomic_agents/lib/components/agent_memory.py) module.

- [AgentMemory](#agentmemory)
  - [AgentMemory](#agentmemory-1)
    - [AgentMemory()._manage_overflow](#agentmemory()_manage_overflow)
    - [AgentMemory().add_message](#agentmemory()add_message)
    - [AgentMemory().copy](#agentmemory()copy)
    - [AgentMemory().dump](#agentmemory()dump)
    - [AgentMemory().get_history](#agentmemory()get_history)
    - [AgentMemory().get_message_count](#agentmemory()get_message_count)
    - [AgentMemory().load](#agentmemory()load)
  - [Message](#message)

## AgentMemory

[Show source in agent_memory.py:23](../../../../../atomic_agents/lib/components/agent_memory.py#L23)

Manages the chat history for an AI agent.

#### Attributes

- `history` *List[Message]* - A list of messages representing the chat history.
- `max_messages` *Optional[int]* - Maximum number of turns to keep in history.

#### Signature

```python
class AgentMemory:
    def __init__(self, max_messages: Optional[int] = None): ...
```

### AgentMemory()._manage_overflow

[Show source in agent_memory.py:71](../../../../../atomic_agents/lib/components/agent_memory.py#L71)

Manages the chat history overflow based on max_messages constraint.

#### Signature

```python
def _manage_overflow(self) -> None: ...
```

### AgentMemory().add_message

[Show source in agent_memory.py:42](../../../../../atomic_agents/lib/components/agent_memory.py#L42)

Adds a message to the chat history and manages overflow.

#### Arguments

- `role` *str* - The role of the message sender.
content (Union[str, Dict]): The content of the message.
- `tool_message` *Optional[Dict]* - Optional tool message to be included.
- `tool_id` *Optional[str]* - Optional unique identifier for the tool call.

#### Signature

```python
def add_message(
    self,
    role: str,
    content: Union[str, Dict],
    tool_message: Optional[Dict] = None,
    tool_id: Optional[str] = None,
) -> None: ...
```

### AgentMemory().copy

[Show source in agent_memory.py:119](../../../../../atomic_agents/lib/components/agent_memory.py#L119)

Creates a copy of the chat memory.

#### Returns

- [AgentMemory](#agentmemory) - A copy of the chat memory.

#### Signature

```python
def copy(self) -> "AgentMemory": ...
```

### AgentMemory().dump

[Show source in agent_memory.py:88](../../../../../atomic_agents/lib/components/agent_memory.py#L88)

Converts the chat history to a list of dictionaries.

#### Returns

- `List[Dict]` - The list of messages as dictionaries.

#### Signature

```python
def dump(self) -> List[Dict]: ...
```

### AgentMemory().get_history

[Show source in agent_memory.py:79](../../../../../atomic_agents/lib/components/agent_memory.py#L79)

Retrieves the chat history.

#### Returns

- `List[Message]` - The list of messages in the chat history.

#### Signature

```python
def get_history(self) -> List[Message]: ...
```

#### See also

- [Message](#message)

### AgentMemory().get_message_count

[Show source in agent_memory.py:131](../../../../../atomic_agents/lib/components/agent_memory.py#L131)

Returns the number of messages in the chat history.

#### Returns

- `int` - The number of messages.

#### Signature

```python
def get_message_count(self) -> int: ...
```

### AgentMemory().load

[Show source in agent_memory.py:97](../../../../../atomic_agents/lib/components/agent_memory.py#L97)

Loads the chat history from a list of dictionaries using Pydantic's parsing.

#### Arguments

- `dict_list` *List[Dict]* - The list of messages as dictionaries.

#### Signature

```python
def load(self, dict_list: List[Dict]) -> None: ...
```



## Message

[Show source in agent_memory.py:6](../../../../../atomic_agents/lib/components/agent_memory.py#L6)

Represents a message in the chat history.

#### Attributes

- `role` *str* - The role of the message sender (e.g., 'user', 'system', 'tool').
content (Union[str, Dict]): The content of the message.
- `tool_calls` *Optional[List[Dict]]* - Optional list of tool call messages.
- `tool_call_id` *Optional[str]* - Optional unique identifier for the tool call.

#### Signature

```python
class Message(BaseModel): ...
```