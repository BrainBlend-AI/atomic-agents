# CalculatorTool

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Tools](./index.md#tools) / CalculatorTool

> Auto-generated documentation for [atomic_agents.lib.tools.calculator_tool](../../../../../atomic_agents/lib/tools/calculator_tool.py) module.

- [CalculatorTool](#calculatortool)
  - [CalculatorTool](#calculatortool-1)
    - [CalculatorTool().run](#calculatortool()run)
  - [CalculatorToolConfig](#calculatortoolconfig)
  - [CalculatorToolOutputSchema](#calculatortooloutputschema)
  - [CalculatorToolSchema](#calculatortoolschema)

## CalculatorTool

[Show source in calculator_tool.py:35](../../../../../atomic_agents/lib/tools/calculator_tool.py#L35)

Tool for performing calculations based on the provided mathematical expression.

#### Attributes

- `input_schema` *CalculatorToolSchema* - The schema for the input data.
- `output_schema` *CalculatorToolOutputSchema* - The schema for the output data.

#### Signature

```python
class CalculatorTool(BaseTool):
    def __init__(self, config: CalculatorToolConfig = CalculatorToolConfig()): ...
```

#### See also

- [BaseTool](./base.md#basetool)
- [CalculatorToolConfig](#calculatortoolconfig)

### CalculatorTool().run

[Show source in calculator_tool.py:55](../../../../../atomic_agents/lib/tools/calculator_tool.py#L55)

Runs the CalculatorTool with the given parameters.

#### Arguments

- `params` *CalculatorToolSchema* - The input parameters for the tool, adhering to the input schema.

#### Returns

- [CalculatorToolOutputSchema](#calculatortooloutputschema) - The output of the tool, adhering to the output schema.

#### Raises

- `ValueError` - If there is an error evaluating the expression.

#### Signature

```python
def run(self, params: CalculatorToolSchema) -> CalculatorToolOutputSchema: ...
```

#### See also

- [CalculatorToolOutputSchema](#calculatortooloutputschema)
- [CalculatorToolSchema](#calculatortoolschema)



## CalculatorToolConfig

[Show source in calculator_tool.py:32](../../../../../atomic_agents/lib/tools/calculator_tool.py#L32)

#### Signature

```python
class CalculatorToolConfig(BaseToolConfig): ...
```

#### See also

- [BaseToolConfig](./base.md#basetoolconfig)



## CalculatorToolOutputSchema

[Show source in calculator_tool.py:26](../../../../../atomic_agents/lib/tools/calculator_tool.py#L26)

#### Signature

```python
class CalculatorToolOutputSchema(BaseModel): ...
```



## CalculatorToolSchema

[Show source in calculator_tool.py:12](../../../../../atomic_agents/lib/tools/calculator_tool.py#L12)

#### Signature

```python
class CalculatorToolSchema(BaseModel): ...
```