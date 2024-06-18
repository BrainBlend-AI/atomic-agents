# ChatMemory

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Components](./index.md#components) / ChatMemory

> Auto-generated documentation for [atomic_agents.lib.components.chat_memory](../../../../../atomic_agents/lib/components/chat_memory.py) module.

- [ChatMemory](#chatmemory)
  - [ChatMemory](#chatmemory-1)
    - [ChatMemory().add_message](#chatmemory()add_message)
    - [ChatMemory().copy](#chatmemory()copy)
    - [ChatMemory().dump](#chatmemory()dump)
    - [ChatMemory().get_history](#chatmemory()get_history)
    - [ChatMemory().load](#chatmemory()load)
  - [Message](#message)

## ChatMemory

[Show source in chat_memory.py:20](../../../../../atomic_agents/lib/components/chat_memory.py#L20)

Manages the chat history for an AI agent.

#### Attributes

- `history` *List[Message]* - A list of messages representing the chat history.

#### Signature

```python
class ChatMemory:
    def __init__(self): ...
```

### ChatMemory().add_message

[Show source in chat_memory.py:34](../../../../../atomic_agents/lib/components/chat_memory.py#L34)

Adds a message to the chat history.

#### Arguments

- `role` *str* - The role of the message sender.
- `content` *str* - The content of the message.
- `tool_message` *Optional[Dict]* - Optional tool message to be included.
- `tool_id` *Optional[str]* - Optional unique identifier for the tool call.

#### Signature

```python
def add_message(
    self,
    role: str,
    content: str,
    tool_message: Optional[Dict] = None,
    tool_id: Optional[str] = None,
) -> None: ...
```

### ChatMemory().copy

[Show source in chat_memory.py:82](../../../../../atomic_agents/lib/components/chat_memory.py#L82)

Creates a copy of the chat memory.

#### Returns

- [ChatMemory](#chatmemory) - A copy of the chat memory.

#### Signature

```python
def copy(self) -> "ChatMemory": ...
```

### ChatMemory().dump

[Show source in chat_memory.py:64](../../../../../atomic_agents/lib/components/chat_memory.py#L64)

Converts the chat history to a list of dictionaries.

#### Returns

- `List[Dict]` - The list of messages as dictionaries.

#### Signature

```python
def dump(self) -> List[Dict]: ...
```

### ChatMemory().get_history

[Show source in chat_memory.py:55](../../../../../atomic_agents/lib/components/chat_memory.py#L55)

Retrieves the chat history.

#### Returns

- `List[Message]` - The list of messages in the chat history.

#### Signature

```python
def get_history(self) -> List[Message]: ...
```

#### See also

- [Message](#message)

### ChatMemory().load

[Show source in chat_memory.py:73](../../../../../atomic_agents/lib/components/chat_memory.py#L73)

Loads the chat history from a list of dictionaries.

#### Arguments

- `dict_list` *List[Dict]* - The list of messages as dictionaries.

#### Signature

```python
def load(self, dict_list: List[Dict]) -> None: ...
```



## Message

[Show source in chat_memory.py:5](../../../../../atomic_agents/lib/components/chat_memory.py#L5)

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