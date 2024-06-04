import os
from typing import Optional
import openai
from pydantic import BaseModel, Field
from sympy import sympify
import instructor
from openai import OpenAI

from atomic_agents.lib.tools.base import BaseTool

################
# INPUT SCHEMA #
################
class CalculatorToolSchema(BaseModel):
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
class CalculatorToolOutputSchema(BaseModel):
    result: str = Field(..., description="Result of the calculation.")

################
# TOOL LOGIC   #
################
class CalculatorTool(BaseTool):
    input_schema = CalculatorToolSchema
    output_schema = CalculatorToolOutputSchema
    
    def __init__(self, tool_description_override: Optional[str] = None):
        super().__init__(tool_description_override)

    def run(self, params: CalculatorToolSchema) -> CalculatorToolOutputSchema:
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
    
    # Initialize the client outside
    client = instructor.from_openai(
        openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
    )
    
    # Extract structured data from natural language
    result = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_model=CalculatorTool.input_schema,
        messages=[{"role": "user", "content": "Calculate 2 + 2"}],
    )

    # Print the result
    print(CalculatorTool().run(result))