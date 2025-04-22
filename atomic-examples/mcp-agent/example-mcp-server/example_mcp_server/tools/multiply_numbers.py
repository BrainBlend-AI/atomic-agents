"""Tool for multiplying two numbers."""

from typing import Dict, Any, Union

from pydantic import Field, BaseModel, ConfigDict

from ..interfaces.tool import Tool, BaseToolInput, ToolResponse


class MultiplyNumbersInput(BaseToolInput):
    """Input schema for the MultiplyNumbers tool."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"number1": 5, "number2": 3}, {"number1": -2.5, "number2": 4}]})

    number1: float = Field(description="The first number to multiply", examples=[5, -2.5])
    number2: float = Field(description="The second number to multiply", examples=[3, 4])


class MultiplyNumbersOutput(BaseModel):
    """Output schema for the MultiplyNumbers tool."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"product": 15, "error": None}, {"product": -10.0, "error": None}]}
    )

    product: float = Field(description="The product of the two numbers (number1 * number2)")
    error: Union[str, None] = Field(default=None, description="An error message if the operation failed.")


class MultiplyNumbersTool(Tool):
    """Tool that multiplies two numbers together."""

    name = "MultiplyNumbers"
    description = "Multiplies two numbers (number1 * number2) and returns the product"
    input_model = MultiplyNumbersInput
    output_model = MultiplyNumbersOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: MultiplyNumbersInput) -> ToolResponse:
        """Execute the multiply numbers tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response containing the product
        """
        result = input_data.number1 * input_data.number2
        output = MultiplyNumbersOutput(product=result, error=None)
        return ToolResponse.from_model(output)
