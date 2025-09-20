"""Sample text resource."""

from typing import Dict, Any, Union

from pydantic import Field, BaseModel, ConfigDict

from ..interfaces.resource import Resource, BaseResourceInput, ResourceResponse
from urllib.parse import unquote as decode_uri


class TestWeatherInput(BaseResourceInput):
    """Input schema for the TestWeatherResource."""

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"country": "USA", "city": "New York"}, {"country": "Canada", "city": "Toronto"}]}
    )

    country: str = Field(description="The country name", examples=["USA", "Canada"])
    city: str = Field(description="The city name", examples=["New York", "Toronto"])


class TestWeatherOutput(BaseModel):
    """Output schema for the TestWeatherResource."""

    model_config = ConfigDict(json_schema_extra={"examples": [{"weather": "72 F and pleasant", "error": None}]})

    weather: str = Field(description="The weather information")
    error: Union[str, None] = Field(default=None, description="An error message if the operation failed.")


class TestWeatherResource(Resource):
    """A sample weather resource that returns static weather content."""

    name = "TestWeatherService"
    description = "Fetch weather based on country and city name."
    uri = "resource://weather/{country}/{city}"
    mime_type = "text/plain"
    input_model = TestWeatherInput
    output_model = TestWeatherOutput

    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this resource."""
        schema = {
            "name": self.name,
            "description": self.description,
            "uri": self.uri,
            "mime_type": self.mime_type,
            "input": self.input_model.model_json_schema(),
        }

        if self.output_model:
            schema["output"] = self.output_model.model_json_schema()

        return schema

    async def read(self, input_data: TestWeatherInput) -> ResourceResponse:
        """Execute the weather resource.

        Args:
            input_data: The validated input for the resource

        Returns:
            A response containing the weather information
        """
        city = decode_uri(input_data.city.title())
        country = decode_uri(input_data.country)
        weather_info = f"Temperature in {city}, {country} is 72 F and pleasant."
        output = TestWeatherOutput(weather=weather_info, error=None)
        return ResourceResponse.from_model(output)
