import pytest
from atomic_agents.lib.tools.calculator_tool import CalculatorTool, CalculatorToolSchema, CalculatorToolOutputSchema, CalculatorToolConfig
from atomic_agents.lib.tools.base_tool import BaseTool, BaseToolConfig

def test_calculator_tool_initialization():
    tool = CalculatorTool()
    assert isinstance(tool, BaseTool)
    assert tool.tool_name == "CalculatorTool"
    assert "Tool for performing calculations" in tool.tool_description

def test_calculator_tool_with_custom_config():
    config = CalculatorToolConfig(title="Custom Calculator", description="Custom description")
    tool = CalculatorTool(config=config)
    assert tool.tool_name == "Custom Calculator"
    assert tool.tool_description == "Custom description"

def test_calculator_tool_input_schema():
    tool = CalculatorTool()
    assert tool.input_schema == CalculatorToolSchema

def test_calculator_tool_output_schema():
    tool = CalculatorTool()
    assert tool.output_schema == CalculatorToolOutputSchema

@pytest.mark.parametrize("expression, expected_result", [
    ("2 + 2", "4.00000000000000"),
    ("3 * 4", "12.0000000000000"),
    ("10 / 2", "5.00000000000000"),
    ("2 ** 3", "8.00000000000000"),
    ("sin(pi/2)", "1.00000000000000"),
    ("log(E)", "1.00000000000000"),  # Changed from "log(e)" to "log(E)"
])
def test_calculator_tool_run_valid_expressions(expression, expected_result):
    tool = CalculatorTool()
    result = tool.run(CalculatorToolSchema(expression=expression))
    assert isinstance(result, CalculatorToolOutputSchema)
    assert result.result == expected_result

def test_calculator_tool_run_complex_expression():
    tool = CalculatorTool()
    expression = "sqrt(3**2 + 4**2)"
    result = tool.run(CalculatorToolSchema(expression=expression))
    assert isinstance(result, CalculatorToolOutputSchema)
    assert result.result == "5.00000000000000"

def test_calculator_tool_run_invalid_expression():
    tool = CalculatorTool()
    invalid_expression = "invalid + expression"
    result = tool.run(CalculatorToolSchema(expression=invalid_expression))
    assert isinstance(result, CalculatorToolOutputSchema)
    assert set(result.result.split(' + ')) == set(invalid_expression.split(' + '))

def test_calculator_tool_run_division_by_zero():
    tool = CalculatorTool()
    result = tool.run(CalculatorToolSchema(expression="1/0"))
    assert isinstance(result, CalculatorToolOutputSchema)
    assert result.result == "zoo"  # SymPy returns "zoo" for complex infinity

def test_calculator_tool_run_with_variables():
    tool = CalculatorTool()
    result = tool.run(CalculatorToolSchema(expression="x + y"))
    assert isinstance(result, CalculatorToolOutputSchema)
    assert result.result == "x + y"  # The tool doesn't evaluate expressions with variables

def test_calculator_tool_config_is_pydantic_model():
    assert issubclass(CalculatorToolConfig, BaseToolConfig)

def test_calculator_tool_config_optional_fields():
    config = CalculatorToolConfig()
    assert hasattr(config, 'title')
    assert hasattr(config, 'description')

