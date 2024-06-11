# ToolInterfaceAgent

[Atomic_agents Index](../../README.md#atomic_agents-index) / [Atomic Agents](../index.md#atomic-agents) / [Agents](./index.md#agents) / ToolInterfaceAgent

> Auto-generated documentation for [atomic_agents.agents.tool_interface_agent](../../../../atomic_agents/agents/tool_interface_agent.py) module.

- [ToolInterfaceAgent](#toolinterfaceagent)
  - [ToolInterfaceAgent](#toolinterfaceagent-1)
    - [ToolInterfaceAgent()._get_and_handle_response](#toolinterfaceagent()_get_and_handle_response)
  - [ToolInterfaceAgentConfig](#toolinterfaceagentconfig)

## ToolInterfaceAgent

[Show source in tool_interface_agent.py:14](../../../../atomic_agents/agents/tool_interface_agent.py#L14)

A specialized chat agent designed to interact with a specific tool.

This agent extends the BaseChatAgent to include functionality for interacting with a tool instance.
It generates system prompts, handles tool input and output, and can optionally return raw tool output.

#### Attributes

- `tool_instance` - The instance of the tool this agent will interact with.
- `return_raw_output` *bool* - Whether to return the raw output from the tool.

#### Signature

```python
class ToolInterfaceAgent(BaseChatAgent):
    def __init__(self, config: ToolInterfaceAgentConfig): ...
```

#### See also

- [BaseChatAgent](./base_chat_agent.md#basechatagent)
- [ToolInterfaceAgentConfig](#toolinterfaceagentconfig)

### ToolInterfaceAgent()._get_and_handle_response

[Show source in tool_interface_agent.py:73](../../../../atomic_agents/agents/tool_interface_agent.py#L73)

Handles obtaining and processing the response from the tool.

This method gets the response from the tool, formats the tool input, adds it to memory,
runs the tool, and processes the tool output. If `return_raw_output` is True, it returns
the raw tool output; otherwise, it processes the output and returns the response.

#### Returns

- `BaseModel` - The processed response or raw tool output.

#### Signature

```python
def _get_and_handle_response(self): ...
```



## ToolInterfaceAgentConfig

[Show source in tool_interface_agent.py:9](../../../../atomic_agents/agents/tool_interface_agent.py#L9)

#### Signature

```python
class ToolInterfaceAgentConfig(BaseChatAgentConfig): ...
```

#### See also

- [BaseChatAgentConfig](./base_chat_agent.md#basechatagentconfig)