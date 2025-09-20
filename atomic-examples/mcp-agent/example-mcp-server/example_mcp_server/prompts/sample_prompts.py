"""Sample prompt implementations."""

from typing import Dict, Any, Union
from pydantic import Field, BaseModel, ConfigDict

from ..interfaces.prompt import Prompt, BasePromptInput, PromptResponse


class GreetingInput(BasePromptInput):
    """Input schema for the GreetingPrompt."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"name": "Alice"}, {"name": "Bob"}]})

    name: str = Field(description="The name of the person to greet", examples=["Alice", "Bob"])


class GreetingOutput(BaseModel):
    """Output schema for the GreetingPrompt."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"content": "Hello Alice, welcome!"},
                {"content": "Hello Bob, welcome!"},
            ]
        }
    )

    content: str = Field(description="The generated greeting message")
    error: Union[str, None] = Field(default=None, description="An error message if the operation failed.")


class GreetingPrompt(Prompt):
    """A prompt that greets the user by name."""

    name = "GreetingPrompt"
    description = "Generate a prompt that greets the user by name"
    input_model = GreetingInput
    output_model = GreetingOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this prompt."""
        schema = {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
        }

        if self.output_model:
            schema["output"] = self.output_model.model_json_schema()

        return schema

    async def generate(self, input_data: GreetingInput, **kwargs) -> PromptResponse:
        """Execute the greeting prompt.

        Args:
            input_data: The validated input for the prompt

        Returns:
            A response containing the greeting message
        """
        greeting_input = GreetingInput.model_validate(input_data.model_dump())
        content = f"Hello {greeting_input.name.title()}, welcome to the project!"
        output = GreetingOutput(content=content, error=None)
        return PromptResponse.from_model(output)
