"""Tool for subtracting two numbers."""

from typing import Dict, Any

from pydantic import Field, BaseModel, ConfigDict

from ..interfaces.tool import Tool, BaseToolInput, ToolResponse


class SubtractionInput(BaseToolInput):
    """Input schema for the Subtraction tool."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"number1": 5, "number2": 3}, {"number1": 1.5, "number2": -2.5}]}
    )

    number1: float = Field(description="The first number", examples=[5, 1.5])
    number2: float = Field(description="The second number", examples=[3, -2.5])


class SubtractionOutput(BaseModel):
    """Output schema for the Subtraction tool."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"difference": 2}, {"difference": 4.0}]})

    difference: float = Field(description="The result of number1 - number2")


class SubtractionTool(Tool):
    """Tool that subtracts two numbers."""

    name = "Subtraction"
    description = "Subtracts two numbers (number1 - number2) and returns the difference"
    input_model = SubtractionInput
    output_model = SubtractionOutput

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: SubtractionInput) -> ToolResponse:
        result = input_data.number1 - input_data.number2
        output = SubtractionOutput(difference=result)
        return ToolResponse.from_model(output)
