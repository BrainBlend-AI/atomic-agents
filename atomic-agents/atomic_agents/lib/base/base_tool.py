from typing import Optional, Type
from pydantic import BaseModel

from atomic_agents.agents.base_agent import BaseIOSchema


class BaseToolConfig(BaseModel):
    """
    Configuration for a tool.

    Attributes:
        title (Optional[str]): Overrides the default title of the tool.
        description (Optional[str]): Overrides the default description of the tool.
    """

    title: Optional[str] = None
    description: Optional[str] = None


class BaseTool:
    """
    Base class for tools within the Atomic Agents framework.

    Attributes:
        input_schema (Type[BaseIOSchema]): Schema defining the input data.
        output_schema (Type[BaseIOSchema]): Schema defining the output data.
        tool_name (str): The name of the tool, derived from the input schema's title.
        tool_description (str): Description of the tool, derived from the input schema's description or overridden by the user.
    """

    input_schema: Type[BaseIOSchema]
    output_schema: Type[BaseIOSchema]

    def __init__(self, config: BaseToolConfig = BaseToolConfig()):
        """
        Initializes the BaseTool with an optional configuration override.

        Args:
            config (BaseToolConfig, optional): Configuration for the tool, including optional title and description overrides.
        """
        self.tool_name = config.title or self.input_schema.model_json_schema()["title"]
        self.tool_description = config.description or self.input_schema.model_json_schema()["description"]

    def run(self, params: Type[BaseIOSchema]) -> BaseIOSchema:
        """
        Executes the tool with the provided parameters.

        Args:
            params (BaseIOSchema): Input parameters adhering to the input schema.

        Returns:
            BaseIOSchema: Output resulting from executing the tool, adhering to the output schema.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement this method")
