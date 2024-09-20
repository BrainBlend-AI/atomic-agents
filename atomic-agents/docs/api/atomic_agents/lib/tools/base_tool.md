# BaseTool

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Tools](./index.md#tools) / BaseTool

> Auto-generated documentation for [atomic_agents.lib.tools.base_tool](../../../../../atomic_agents/lib/tools/base_tool.py) module.

- [BaseTool](#basetool)
  - [BaseTool](#basetool-1)
    - [BaseTool().run](#basetool()run)
  - [BaseToolConfig](#basetoolconfig)

## BaseTool

[Show source in base_tool.py:13](../../../../../atomic_agents/lib/tools/base_tool.py#L13)

Base class for all tools in the Atomic Agents framework.

#### Attributes

- `input_schema` *Type[BaseIOSchema]* - The schema for the input data.
- `output_schema` *Type[BaseIOSchema]* - The schema for the output data.
- `tool_name` *str* - The name of the tool, derived from the input schema's title.
tool_description (str):
    The description of the tool, derived from the input schema's description or overridden by the user.

#### Signature

```python
class BaseTool:
    def __init__(self, config: BaseToolConfig = BaseToolConfig()): ...
```

#### See also

- [BaseToolConfig](#basetoolconfig)

### BaseTool().run

[Show source in base_tool.py:38](../../../../../atomic_agents/lib/tools/base_tool.py#L38)

Runs the tool with the given parameters. This method should be implemented by subclasses.

#### Arguments

- `params` *BaseIOSchema* - The input parameters for the tool, adhering to the input schema.

#### Returns

- `BaseIOSchema` - The output of the tool, adhering to the output schema.

#### Raises

- `NotImplementedError` - If the method is not implemented by a subclass.

#### Signature

```python
def run(self, params: Type[BaseIOSchema]) -> BaseIOSchema: ...
```

#### See also

- [BaseIOSchema](../../agents/base_agent.md#baseioschema)



## BaseToolConfig

[Show source in base_tool.py:8](../../../../../atomic_agents/lib/tools/base_tool.py#L8)

#### Signature

```python
class BaseToolConfig(BaseModel): ...
```