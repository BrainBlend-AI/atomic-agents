"""Tool for dividing two numbers."""

from typing import Dict, Any

from pydantic import Field, BaseModel, ConfigDict

from ..interfaces.tool import Tool, BaseToolInput, ToolResponse


class DivisionInput(BaseToolInput):
    """Input schema for the Division tool."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"number1": 8, "number2": 2}, {"number1": 5, "number2": -2.5}]})

    number1: float = Field(description="The numerator", examples=[8, 5])
    number2: float = Field(description="The denominator (must not be zero)", examples=[2, -2.5])


class DivisionOutput(BaseModel):
    """Output schema for the Division tool."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"quotient": 4}, {"quotient": -2.0}]})

    quotient: float = Field(description="The result of number1 / number2")


class DivisionTool(Tool):
    """Tool that divides two numbers."""

    name = "Division"
    description = "Divides two numbers (number1 / number2) and returns the quotient"
    input_model = DivisionInput
    output_model = DivisionOutput

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: DivisionInput) -> ToolResponse:
        if input_data.number2 == 0:
            raise ValueError("Division by zero is not allowed")
        result = input_data.number1 / input_data.number2
        output = DivisionOutput(quotient=result)
        return ToolResponse.from_model(output)
