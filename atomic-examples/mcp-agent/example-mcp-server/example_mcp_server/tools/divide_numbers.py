"""Tool for dividing two numbers."""

from typing import Dict, Any, Union

from pydantic import Field, BaseModel, ConfigDict

from ..interfaces.tool import Tool, BaseToolInput, ToolResponse


class DivideNumbersInput(BaseToolInput):
    """Input schema for the DivideNumbers tool."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"dividend": 10, "divisor": 2}, {"dividend": 5, "divisor": 0}, {"dividend": 7.5, "divisor": 2.5}]
        }
    )

    dividend: float = Field(description="The number to be divided", examples=[10, 5, 7.5])
    divisor: float = Field(description="The number to divide by", examples=[2, 0, 2.5])


class DivideNumbersOutput(BaseModel):
    """Output schema for the DivideNumbers tool."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"quotient": 5.0}, {"error": "Division by zero is not allowed."}, {"quotient": 3.0}]}
    )

    quotient: Union[float, None] = Field(
        default=None, description="The result of the division (dividend / divisor). None if division by zero occurred."
    )
    error: Union[str, None] = Field(
        default=None, description="An error message if the operation failed (e.g., division by zero)."
    )


class DivideNumbersTool(Tool):
    """Tool that divides one number by another."""

    name = "DivideNumbers"
    description = "Divides the first number (dividend) by the second number (divisor) and returns the quotient. Handles division by zero."
    input_model = DivideNumbersInput
    output_model = DivideNumbersOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: DivideNumbersInput) -> ToolResponse:
        """Execute the divide numbers tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response containing the quotient or an error message
        """
        if input_data.divisor == 0:
            output = DivideNumbersOutput(error="Division by zero is not allowed.")
            # Optionally set a specific status code if your ToolResponse supports it
            # return ToolResponse(status_code=400, content=ToolContent.from_model(output))
            return ToolResponse.from_model(output)
        else:
            result = input_data.dividend / input_data.divisor
            output = DivideNumbersOutput(quotient=result)
            return ToolResponse.from_model(output)
