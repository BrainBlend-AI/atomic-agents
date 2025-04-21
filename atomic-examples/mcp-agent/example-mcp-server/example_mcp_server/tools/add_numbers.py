"""Tool for adding two numbers."""

from typing import Dict, Any, Union

from pydantic import Field, BaseModel, ConfigDict

from ..interfaces.tool import Tool, BaseToolInput, ToolResponse


class AddNumbersInput(BaseToolInput):
    """Input schema for the AddNumbers tool."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"number1": 5, "number2": 3}, {"number1": -2.5, "number2": 1.5}]}
    )

    number1: float = Field(description="The first number to add", examples=[5, -2.5])
    number2: float = Field(description="The second number to add", examples=[3, 1.5])


class AddNumbersOutput(BaseModel):
    """Output schema for the AddNumbers tool."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"sum": 8, "error": None}, {"sum": -1.0, "error": None}]})

    sum: float = Field(description="The sum of the two numbers")
    error: Union[str, None] = Field(default=None, description="An error message if the operation failed.")


class AddNumbersTool(Tool):
    """Tool that adds two numbers together."""

    name = "AddNumbers"
    description = "Adds two numbers (number1 + number2) and returns the sum"
    input_model = AddNumbersInput
    output_model = AddNumbersOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: AddNumbersInput) -> ToolResponse:
        """Execute the add numbers tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response containing the sum
        """
        result = input_data.number1 + input_data.number2
        output = AddNumbersOutput(sum=result, error=None)
        return ToolResponse.from_model(output)
