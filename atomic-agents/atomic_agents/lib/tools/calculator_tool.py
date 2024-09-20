from pydantic import Field
from rich.console import Console
from sympy import sympify

from atomic_agents.agents.base_agent import BaseIOSchema
from atomic_agents.lib.tools.base_tool import BaseTool, BaseToolConfig


################
# INPUT SCHEMA #
################
class CalculatorToolInputSchema(BaseIOSchema):
    """
    Tool for performing calculations. Supports basic arithmetic operations
    like addition, subtraction, multiplication, and division, but also more
    complex operations like exponentiation and trigonometric functions.
    Use this tool to evaluate mathematical expressions.
    """

    expression: str = Field(..., description="Mathematical expression to evaluate. For example, '2 + 2'.")


####################
# OUTPUT SCHEMA(S) #
####################
class CalculatorToolOutputSchema(BaseIOSchema):
    """This schema defines the output of the CalculatorTool."""

    result: str = Field(..., description="Result of the calculation.")


##############
# TOOL LOGIC #
##############
class CalculatorToolConfig(BaseToolConfig):
    pass


class CalculatorTool(BaseTool):
    """
    Tool for performing calculations based on the provided mathematical expression.

    Attributes:
        input_schema (CalculatorToolInputSchema): The schema for the input data.
        output_schema (CalculatorToolOutputSchema): The schema for the output data.
    """

    input_schema = CalculatorToolInputSchema
    output_schema = CalculatorToolOutputSchema

    def __init__(self, config: CalculatorToolConfig = CalculatorToolConfig()):
        """
        Initializes the CalculatorTool.

        Args:
            config (CalculatorToolConfig): Configuration for the tool.
        """
        super().__init__(config)

    def run(self, params: CalculatorToolInputSchema) -> CalculatorToolOutputSchema:
        """
        Runs the CalculatorTool with the given parameters.

        Args:
            params (CalculatorToolInputSchema): The input parameters for the tool, adhering to the input schema.

        Returns:
            CalculatorToolOutputSchema: The output of the tool, adhering to the output schema.
        """
        # Explicitly convert the string form of the expression
        parsed_expr = sympify(str(params.expression))
        # Evaluate the expression numerically
        result = parsed_expr.evalf()
        return CalculatorToolOutputSchema(result=str(result))


#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    rich_console = Console()
    rich_console.print(CalculatorTool().run(CalculatorToolInputSchema(expression="2 + 2")))
