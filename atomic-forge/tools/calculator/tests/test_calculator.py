import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tool.calculator import (  # noqa: E402
    CalculatorTool,
    CalculatorToolInputSchema,
    CalculatorToolOutputSchema,
)


def test_calculator_tool():
    calculator_tool = CalculatorTool()
    input_schema = CalculatorToolInputSchema(expression="2 + 2")
    result = calculator_tool.run(input_schema)
    assert result == CalculatorToolOutputSchema(result="4.00000000000000")


if __name__ == "__main__":
    test_calculator_tool()
