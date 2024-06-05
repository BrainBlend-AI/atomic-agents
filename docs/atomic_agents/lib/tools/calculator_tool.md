# CalculatorTool

[Atomic_agents_redux Index](../../../README.md#atomic_agents_redux-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Creating a New Tool](./index.md#creating-a-new-tool) / CalculatorTool

> Auto-generated documentation for [atomic_agents.lib.tools.calculator_tool](../../../../atomic_agents/lib/tools/calculator_tool.py) module.

#### Attributes

- `client` - Initialize the client outside: instructor.from_openai(openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'), base_url=os.getenv('OPENAI_BASE_URL')))

- `result` - Extract structured data from natural language: client.chat.completions.create(model='gpt-3.5-turbo', response_model=CalculatorTool.input_schema, messages=[{'role': 'user', 'content': 'Calculate 2 + 2'}])


- [CalculatorTool](#calculatortool)
  - [CalculatorTool](#calculatortool-1)
    - [CalculatorTool().run](#calculatortool()run)
  - [CalculatorToolOutputSchema](#calculatortooloutputschema)
  - [CalculatorToolSchema](#calculatortoolschema)

## CalculatorTool

[Show source in calculator_tool.py:32](../../../../atomic_agents/lib/tools/calculator_tool.py#L32)

Tool for performing calculations based on the provided mathematical expression.

#### Attributes

- `input_schema` *CalculatorToolSchema* - The schema for the input data.
- `output_schema` *CalculatorToolOutputSchema* - The schema for the output data.

#### Signature

```python
class CalculatorTool(BaseTool):
    def __init__(self, *args, **kwargs): ...
```

#### See also

- [BaseTool](./base.md#basetool)

### CalculatorTool().run

[Show source in calculator_tool.py:53](../../../../atomic_agents/lib/tools/calculator_tool.py#L53)

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



## CalculatorToolOutputSchema

[Show source in calculator_tool.py:26](../../../../atomic_agents/lib/tools/calculator_tool.py#L26)

#### Signature

```python
class CalculatorToolOutputSchema(BaseModel): ...
```



## CalculatorToolSchema

[Show source in calculator_tool.py:12](../../../../atomic_agents/lib/tools/calculator_tool.py#L12)

#### Signature

```python
class CalculatorToolSchema(BaseModel): ...
```