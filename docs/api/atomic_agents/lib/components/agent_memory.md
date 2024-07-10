# AgentMemory

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Components](./index.md#components) / AgentMemory

> Auto-generated documentation for [atomic_agents.lib.components.agent_memory](../../../../../atomic_agents/lib/components/agent_memory.py) module.

#### Attributes

- `memory` - Create a AgentMemory with a maximum of 5 messages: AgentMemory(max_messages=5)

- `content` - Test Case 1: Text()

- `content` - Test Case 2: Text()

- `content` - Test Case 3: Text()

- `content` - Test Case 4: Text()

- `content` - Test Case 5: Text()

- `content` - Test Case 6: Text()

- `content` - Test Case 7: Text()

- `content` - Test Case 8: Text()


- [AgentMemory](#AgentMemory)
  - [AgentMemory](#AgentMemory-1)
    - [AgentMemory()._manage_overflow](#AgentMemory()_manage_overflow)
    - [AgentMemory().add_message](#AgentMemory()add_message)
    - [AgentMemory().copy](#AgentMemory()copy)
    - [AgentMemory().dump](#AgentMemory()dump)
    - [AgentMemory().get_history](#AgentMemory()get_history)
    - [AgentMemory().get_message_count](#AgentMemory()get_message_count)
    - [AgentMemory().load](#AgentMemory()load)
  - [Message](#message)
  - [print_panel](#print_panel)

## AgentMemory

[Show source in agent_memory.py:19](../../../../../atomic_agents/lib/components/agent_memory.py#L19)

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

[Show source in agent_memory.py:61](../../../../../atomic_agents/lib/components/agent_memory.py#L61)

Manages the chat history overflow based on max_messages constraint.

#### Signature

```python
def _manage_overflow(self) -> None: ...
```

### AgentMemory().add_message

[Show source in agent_memory.py:38](../../../../../atomic_agents/lib/components/agent_memory.py#L38)

Adds a message to the chat history and manages overflow.

#### Arguments

- `role` *str* - The role of the message sender.
content (Union[str, Dict]): The content of the message.
- [tool_message](#AgentMemory) *Optional[Dict]* - Optional tool message to be included.
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

[Show source in agent_memory.py:109](../../../../../atomic_agents/lib/components/agent_memory.py#L109)

Creates a copy of the chat memory.

#### Returns

- [AgentMemory](#AgentMemory) - A copy of the chat memory.

#### Signature

```python
def copy(self) -> "AgentMemory": ...
```

### AgentMemory().dump

[Show source in agent_memory.py:78](../../../../../atomic_agents/lib/components/agent_memory.py#L78)

Converts the chat history to a list of dictionaries.

#### Returns

- `List[Dict]` - The list of messages as dictionaries.

#### Signature

```python
def dump(self) -> List[Dict]: ...
```

### AgentMemory().get_history

[Show source in agent_memory.py:69](../../../../../atomic_agents/lib/components/agent_memory.py#L69)

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

[Show source in agent_memory.py:121](../../../../../atomic_agents/lib/components/agent_memory.py#L121)

Returns the number of messages in the chat history.

#### Returns

- `int` - The number of messages.

#### Signature

```python
def get_message_count(self) -> int: ...
```

### AgentMemory().load

[Show source in agent_memory.py:87](../../../../../atomic_agents/lib/components/agent_memory.py#L87)

Loads the chat history from a list of dictionaries using Pydantic's parsing.

#### Arguments

- `dict_list` *List[Dict]* - The list of messages as dictionaries.

#### Signature

```python
def load(self, dict_list: List[Dict]) -> None: ...
```



## Message

[Show source in agent_memory.py:4](../../../../../atomic_agents/lib/components/agent_memory.py#L4)

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



## print_panel

[Show source in agent_memory.py:139](../../../../../atomic_agents/lib/components/agent_memory.py#L139)

#### Signature

```python
def print_panel(title, content): ...
```