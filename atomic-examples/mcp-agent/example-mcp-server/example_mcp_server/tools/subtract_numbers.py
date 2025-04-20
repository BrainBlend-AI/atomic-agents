"""Tool for subtracting two numbers."""

from typing import Dict, Any, Union

from pydantic import Field, BaseModel, ConfigDict

from ..interfaces.tool import Tool, BaseToolInput, ToolResponse


class SubtractNumbersInput(BaseToolInput):
    """Input schema for the SubtractNumbers tool."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"number1": 5, "number2": 3}, {"number1": 1.5, "number2": 2.5}]})

    number1: float = Field(description="The number to subtract from", examples=[5, 1.5])
    number2: float = Field(description="The number to subtract", examples=[3, 2.5])


class SubtractNumbersOutput(BaseModel):
    """Output schema for the SubtractNumbers tool."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"difference": 2, "error": None}, {"difference": -1.0, "error": None}]}
    )

    difference: float = Field(description="The difference between the two numbers (number1 - number2)")
    error: Union[str, None] = Field(default=None, description="An error message if the operation failed.")


class SubtractNumbersTool(Tool):
    """Tool that subtracts one number from another."""

    name = "SubtractNumbers"
    description = "Subtracts the second number from the first number (number1 - number2) and returns the difference"
    input_model = SubtractNumbersInput
    output_model = SubtractNumbersOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: SubtractNumbersInput) -> ToolResponse:
        """Execute the subtract numbers tool.

        Args:
            input_data: The validated input for the tool

        Returns:
            A response containing the difference
        """
        result = input_data.number1 - input_data.number2
        output = SubtractNumbersOutput(difference=result, error=None)
        return ToolResponse.from_model(output)
