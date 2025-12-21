"""Example API tool with proper error handling and configuration."""

import os
import requests
from typing import Optional, List

from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field


# ============================================================
# Schemas
# ============================================================

class WeatherInputSchema(BaseIOSchema):
    """Input for weather lookup."""

    city: str = Field(
        ...,
        min_length=1,
        description="City name to get weather for"
    )
    units: str = Field(
        default="metric",
        description="Units: 'metric' (Celsius) or 'imperial' (Fahrenheit)"
    )


class WeatherOutputSchema(BaseIOSchema):
    """Successful weather result."""

    city: str = Field(..., description="City name")
    temperature: float = Field(..., description="Current temperature")
    units: str = Field(..., description="Temperature units")
    conditions: str = Field(..., description="Weather conditions")
    humidity: int = Field(..., description="Humidity percentage")
    wind_speed: float = Field(..., description="Wind speed")


class WeatherErrorSchema(BaseIOSchema):
    """Weather API error."""

    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    city: Optional[str] = Field(default=None, description="Requested city")


# ============================================================
# Configuration
# ============================================================

class WeatherToolConfig(BaseToolConfig):
    """Configuration for Weather Tool."""

    api_key: str = Field(
        default_factory=lambda: os.getenv("OPENWEATHER_API_KEY", ""),
        description="OpenWeatherMap API key"
    )
    base_url: str = Field(
        default="https://api.openweathermap.org/data/2.5",
        description="API base URL"
    )
    timeout: int = Field(
        default=10,
        ge=1,
        le=60,
        description="Request timeout in seconds"
    )


# ============================================================
# Tool Implementation
# ============================================================

class WeatherTool(BaseTool):
    """
    Tool for fetching current weather conditions.

    Uses the OpenWeatherMap API to get current weather data
    for a specified city.

    Requires OPENWEATHER_API_KEY environment variable.
    """

    input_schema = WeatherInputSchema
    output_schema = WeatherOutputSchema

    def __init__(self, config: WeatherToolConfig = None):
        """Initialize the weather tool."""
        super().__init__(config or WeatherToolConfig())
        self.config: WeatherToolConfig = self.config

    def run(
        self, params: WeatherInputSchema
    ) -> WeatherOutputSchema | WeatherErrorSchema:
        """
        Fetch weather for a city.

        Args:
            params: Input parameters with city and units

        Returns:
            WeatherOutputSchema on success, WeatherErrorSchema on failure
        """
        # Validate configuration
        if not self.config.api_key:
            return WeatherErrorSchema(
                error="OpenWeatherMap API key not configured",
                code="CONFIG_ERROR",
                city=params.city
            )

        try:
            # Make API request
            response = requests.get(
                f"{self.config.base_url}/weather",
                params={
                    "q": params.city,
                    "appid": self.config.api_key,
                    "units": params.units,
                },
                timeout=self.config.timeout,
            )

            # Handle HTTP errors
            if response.status_code == 404:
                return WeatherErrorSchema(
                    error=f"City '{params.city}' not found",
                    code="CITY_NOT_FOUND",
                    city=params.city
                )

            response.raise_for_status()
            data = response.json()

            # Parse response
            return WeatherOutputSchema(
                city=data["name"],
                temperature=data["main"]["temp"],
                units="°C" if params.units == "metric" else "°F",
                conditions=data["weather"][0]["description"],
                humidity=data["main"]["humidity"],
                wind_speed=data["wind"]["speed"],
            )

        except requests.Timeout:
            return WeatherErrorSchema(
                error="Request timed out",
                code="TIMEOUT",
                city=params.city
            )
        except requests.HTTPError as e:
            return WeatherErrorSchema(
                error=f"API error: {e}",
                code="HTTP_ERROR",
                city=params.city
            )
        except requests.RequestException as e:
            return WeatherErrorSchema(
                error=f"Network error: {e}",
                code="NETWORK_ERROR",
                city=params.city
            )
        except KeyError as e:
            return WeatherErrorSchema(
                error=f"Unexpected API response format: missing {e}",
                code="PARSE_ERROR",
                city=params.city
            )
        except Exception as e:
            return WeatherErrorSchema(
                error=f"Unexpected error: {e}",
                code="UNKNOWN_ERROR",
                city=params.city
            )


# ============================================================
# Convenience Instance
# ============================================================

# Default instance with environment-based config
weather_tool = WeatherTool()


# ============================================================
# Usage Example
# ============================================================

if __name__ == "__main__":
    from rich.console import Console
    from rich.table import Table

    console = Console()

    # Create tool
    tool = WeatherTool()

    # Test cities
    cities = ["London", "New York", "Tokyo", "InvalidCity123"]

    table = Table(title="Weather Results")
    table.add_column("City", style="cyan")
    table.add_column("Temperature", style="green")
    table.add_column("Conditions", style="yellow")
    table.add_column("Status", style="bold")

    for city in cities:
        result = tool.run(WeatherInputSchema(city=city))

        if isinstance(result, WeatherErrorSchema):
            table.add_row(city, "-", "-", f"[red]{result.code}[/red]")
        else:
            table.add_row(
                result.city,
                f"{result.temperature}{result.units}",
                result.conditions,
                "[green]OK[/green]"
            )

    console.print(table)
