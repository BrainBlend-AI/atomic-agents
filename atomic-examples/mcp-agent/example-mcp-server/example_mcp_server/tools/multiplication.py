"""Tool for multiplying two numbers."""

from typing import Dict, Any

from pydantic import Field, BaseModel, ConfigDict

from ..interfaces.tool import Tool, BaseToolInput, ToolResponse


class MultiplicationInput(BaseToolInput):
    """Input schema for the Multiplication tool."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"number1": 2, "number2": 4}, {"number1": -1.5, "number2": 3}]})

    number1: float = Field(description="The first number", examples=[2, -1.5])
    number2: float = Field(description="The second number", examples=[4, 3])


class MultiplicationOutput(BaseModel):
    """Output schema for the Multiplication tool."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"product": 8}, {"product": -4.5}]})

    product: float = Field(description="The product of the two numbers")


class MultiplicationTool(Tool):
    """Tool that multiplies two numbers."""

    name = "Multiplication"
    description = "Multiplies two numbers (number1 * number2) and returns the product"
    input_model = MultiplicationInput
    output_model = MultiplicationOutput

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
            "output": self.output_model.model_json_schema(),
        }

    async def execute(self, input_data: MultiplicationInput) -> ToolResponse:
        result = input_data.number1 * input_data.number2
        output = MultiplicationOutput(product=result)
        return ToolResponse.from_model(output)
