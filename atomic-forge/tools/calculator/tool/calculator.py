from typing import Dict, Any
from pydantic import Field
from sympy import sympify

from atomic_agents import BaseIOSchema, BaseTool, BaseToolConfig


################
# INPUT SCHEMA #
################
class CalculatorToolInputSchema(BaseIOSchema):
    """
    Tool for performing calculations. Supports basic arithmetic operations
    like addition, subtraction, multiplication, and division, as well as more
    complex operations like exponentiation and trigonometric functions.
    Use this tool to evaluate mathematical expressions.
    """

    expression: str = Field(..., description="Mathematical expression to evaluate. For example, '2 + 2'.")


#################
# OUTPUT SCHEMA #
#################
class CalculatorToolOutputSchema(BaseIOSchema):
    """
    Schema for the output of the CalculatorTool.
    """

    result: str = Field(..., description="Result of the calculation.")


#################
# CONFIGURATION #
#################
class CalculatorToolConfig(BaseToolConfig):
    """
    Configuration for the CalculatorTool.

    Attributes:
        title (Optional[str]): Overrides the default title of the tool.
        description (Optional[str]): Overrides the default description of the tool.
        safe_mode (bool): Whether to run in safe mode with restricted operations.
        allowed_functions (Dict[str, Any]): Functions to make available in the calculator.
    """

    safe_mode: bool = True
    allowed_functions: Dict[str, Any] = {}


#####################
# MAIN TOOL & LOGIC #
#####################
class CalculatorTool(BaseTool[CalculatorToolInputSchema, CalculatorToolOutputSchema]):
    """
    Tool for evaluating mathematical expressions.

    Attributes:
        input_schema (CalculatorToolInputSchema): Schema defining the input data.
        output_schema (CalculatorToolOutputSchema): Schema defining the output data.
        safe_mode (bool): Whether to run in safe mode with restricted operations.
        allowed_functions (Dict[str, Any]): Functions to make available in the calculator.
    """

    def __init__(self, config: CalculatorToolConfig = CalculatorToolConfig()):
        """
        Initializes the CalculatorTool.

        Args:
            config (CalculatorToolConfig): Configuration for the tool.
        """
        super().__init__(config)
        self.safe_mode = config.safe_mode
        self.allowed_functions = config.allowed_functions

    def run(self, params: CalculatorToolInputSchema) -> CalculatorToolOutputSchema:
        """
        Executes the CalculatorTool with the given parameters.

        Args:
            params (CalculatorToolInputSchema): The input parameters for the tool.

        Returns:
            CalculatorToolOutputSchema: The result of the calculation.
        """
        # Convert the expression string to a symbolic expression
        parsed_expr = sympify(str(params.expression))

        # Evaluate the expression numerically
        result = parsed_expr.evalf()
        return CalculatorToolOutputSchema(result=str(result))


#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    calculator = CalculatorTool()
    result = calculator.run(CalculatorToolInputSchema(expression="sin(pi/2) + cos(pi/4)"))
    print(result)  # Expected output: {"result":"1.70710678118655"}
