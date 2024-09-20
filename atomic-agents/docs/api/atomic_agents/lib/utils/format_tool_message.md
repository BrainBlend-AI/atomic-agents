# Format Tool Message

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Utils](./index.md#utils) / Format Tool Message

> Auto-generated documentation for [atomic_agents.lib.utils.format_tool_message](../../../../../atomic_agents/lib/utils/format_tool_message.py) module.

- [Format Tool Message](#format-tool-message)
  - [format_tool_message](#format_tool_message)

## format_tool_message

[Show source in format_tool_message.py:8](../../../../../atomic_agents/lib/utils/format_tool_message.py#L8)

Formats a message for a tool call.

#### Arguments

- `tool_call` *Type[BaseModel]* - The Pydantic model instance representing the tool call.
- `tool_id` *str, optional* - The unique identifier for the tool call. If not provided, a random UUID will be generated.

#### Returns

- `Dict` - A formatted message dictionary for the tool call.

#### Signature

```python
def format_tool_message(
    tool_call: Type[BaseModel], tool_id: Optional[str] = None
) -> Dict: ...
```