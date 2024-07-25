# CalculatorTool

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Tools](./index.md#tools) / CalculatorTool

> Auto-generated documentation for [atomic_agents.lib.tools.calculator_tool](../../../../../atomic_agents/lib/tools/calculator_tool.py) module.

- [CalculatorTool](#calculatortool)
  - [CalculatorTool](#calculatortool-1)
    - [CalculatorTool().run](#calculatortool()run)
  - [CalculatorToolConfig](#calculatortoolconfig)
  - [CalculatorToolInputSchema](#calculatortoolinputschema)
  - [CalculatorToolOutputSchema](#calculatortooloutputschema)

## CalculatorTool

[Show source in calculator_tool.py:40](../../../../../atomic_agents/lib/tools/calculator_tool.py#L40)

Tool for performing calculations based on the provided mathematical expression.

#### Attributes

- `input_schema` *CalculatorToolInputSchema* - The schema for the input data.
- `output_schema` *CalculatorToolOutputSchema* - The schema for the output data.

#### Signature

```python
class CalculatorTool(BaseTool):
    def __init__(self, config: CalculatorToolConfig = CalculatorToolConfig()): ...
```

#### See also

- [BaseTool](./base_tool.md#basetool)
- [CalculatorToolConfig](#calculatortoolconfig)

### CalculatorTool().run

[Show source in calculator_tool.py:61](../../../../../atomic_agents/lib/tools/calculator_tool.py#L61)

Runs the CalculatorTool with the given parameters.

#### Arguments

- `params` *CalculatorToolInputSchema* - The input parameters for the tool, adhering to the input schema.

#### Returns

- [CalculatorToolOutputSchema](#calculatortooloutputschema) - The output of the tool, adhering to the output schema.

#### Signature

```python
def run(self, params: CalculatorToolInputSchema) -> CalculatorToolOutputSchema: ...
```

#### See also

- [CalculatorToolInputSchema](#calculatortoolinputschema)
- [CalculatorToolOutputSchema](#calculatortooloutputschema)



## CalculatorToolConfig

[Show source in calculator_tool.py:36](../../../../../atomic_agents/lib/tools/calculator_tool.py#L36)

#### Signature

```python
class CalculatorToolConfig(BaseToolConfig): ...
```

#### See also

- [BaseToolConfig](./base_tool.md#basetoolconfig)



## CalculatorToolInputSchema

[Show source in calculator_tool.py:12](../../../../../atomic_agents/lib/tools/calculator_tool.py#L12)

#### Signature

```python
class CalculatorToolInputSchema(BaseIOSchema): ...
```

#### See also

- [BaseIOSchema](../../agents/base_agent.md#baseioschema)



## CalculatorToolOutputSchema

[Show source in calculator_tool.py:29](../../../../../atomic_agents/lib/tools/calculator_tool.py#L29)

#### Signature

```python
class CalculatorToolOutputSchema(BaseIOSchema): ...
```

#### See also

- [BaseIOSchema](../../agents/base_agent.md#baseioschema)