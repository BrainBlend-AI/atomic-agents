"""Tool for adding two numbers."""

from typing import Dict, Any

from pydantic import Field, BaseModel, ConfigDict

from ..interfaces.tool import Tool, BaseToolInput, ToolResponse


class AdditionInput(BaseToolInput):
    """Input schema for the Addition tool."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"number1": 5, "number2": 3}, {"number1": -2.5, "number2": 1.5}]}
    )

    number1: float = Field(description="The first number", examples=[5, -2.5])
    number2: float = Field(description="The second number", examples=[3, 1.5])


class AdditionOutput(BaseModel):
    """Output schema for the Addition tool."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"sum": 8}, {"sum": -1.0}]})

    sum: float = Field(description="The sum of the two numbers")


class AdditionTool(Tool):
    """Tool that adds two numbers."""

    name = "Addition"
    description = "Adds two numbers (number1 + number2) and returns the sum"
    input_model = AdditionInput
    output_model = AdditionOutput

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: AdditionInput) -> ToolResponse:
        result = input_data.number1 + input_data.number2
        output = AdditionOutput(sum=result)
        return ToolResponse.from_model(output)
