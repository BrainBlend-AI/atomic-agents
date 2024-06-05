# Base

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Tools](./index.md#tools) / Base

> Auto-generated documentation for [atomic_agents.lib.tools.base](../../../../atomic_agents/lib/tools/base.py) module.

- [Base](#base)
  - [BaseTool](#basetool)
    - [BaseTool().run](#basetool()run)

## BaseTool

[Show source in base.py:4](../../../../atomic_agents/lib/tools/base.py#L4)

Base class for all tools in the Atomic Agents framework.

#### Attributes

- `input_schema` *Type[BaseModel]* - The schema for the input data.
- `output_schema` *Type[BaseModel]* - The schema for the output data.
- `tool_name` *str* - The name of the tool, derived from the input schema's title.
- `tool_description` *str* - The description of the tool, derived from the input schema's description or overridden by the user.

#### Signature

```python
class BaseTool:
    def __init__(self, tool_description_override: Optional[str] = None): ...
```

### BaseTool().run

[Show source in base.py:28](../../../../atomic_agents/lib/tools/base.py#L28)

Runs the tool with the given parameters. This method should be implemented by subclasses.

#### Arguments

- `params` *BaseModel* - The input parameters for the tool, adhering to the input schema.

#### Returns

- `BaseModel` - The output of the tool, adhering to the output schema.

#### Raises

- `NotImplementedError` - If the method is not implemented by a subclass.

#### Signature

```python
def run(self, params: BaseModel) -> BaseModel: ...
```