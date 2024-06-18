from pydantic import Field
from sympy import sympify
from rich.console import Console

from atomic_agents.agents.base_chat_agent import BaseAgentIO
from atomic_agents.lib.tools.base import BaseTool, BaseToolConfig

################
# INPUT SCHEMA #
################
class CalculatorToolSchema(BaseAgentIO):
    expression: str = Field(..., description="Mathematical expression to evaluate. For example, '2 + 2'.")

    class Config:
        title = "CalculatorTool"
        description = "Tool for performing calculations. Supports basic arithmetic operations like addition, subtraction, multiplication, and division, but also more complex operations like exponentiation and trigonometric functions. Use this tool to evaluate mathematical expressions."
        json_schema_extra = {
            "title": title,
            "description": description
        }
        
####################
# OUTPUT SCHEMA(S) #
####################
class CalculatorToolOutputSchema(BaseAgentIO):
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
        input_schema (CalculatorToolSchema): The schema for the input data.
        output_schema (CalculatorToolOutputSchema): The schema for the output data.
    """
    input_schema = CalculatorToolSchema
    output_schema = CalculatorToolOutputSchema
    
    def __init__(self, config: CalculatorToolConfig = CalculatorToolConfig()):
        """
        Initializes the CalculatorTool.
        
        Args:
            config (CalculatorToolConfig): Configuration for the tool.
        """
        super().__init__(config)

    def run(self, params: CalculatorToolSchema) -> CalculatorToolOutputSchema:
        """
        Runs the CalculatorTool with the given parameters.

        Args:
            params (CalculatorToolSchema): The input parameters for the tool, adhering to the input schema.

        Returns:
            CalculatorToolOutputSchema: The output of the tool, adhering to the output schema.

        Raises:
            ValueError: If there is an error evaluating the expression.
        """
        try:
            # Explicitly convert the string form of the expression
            parsed_expr = sympify(str(params.expression))
            # Evaluate the expression numerically
            result = parsed_expr.evalf()
            return CalculatorToolOutputSchema(result=str(result))
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {e}")
            
            
#################
# EXAMPLE USAGE #
#################
if __name__ == "__main__":
    rich_console = Console()
    rich_console.print(CalculatorTool().run(CalculatorToolSchema(expression="2 + 2")))
