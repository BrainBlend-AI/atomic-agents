from typing import Optional, Type

from pydantic import BaseModel

from atomic_agents.agents.base_agent import BaseIOSchema


class BaseToolConfig(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class BaseTool:
    """
    Base class for all tools in the Atomic Agents framework.

    Attributes:
        input_schema (Type[BaseIOSchema]): The schema for the input data.
        output_schema (Type[BaseIOSchema]): The schema for the output data.
        tool_name (str): The name of the tool, derived from the input schema's title.
        tool_description (str):
            The description of the tool, derived from the input schema's description or overridden by the user.
    """

    input_schema: Type[BaseIOSchema]
    output_schema: Type[BaseIOSchema]

    def __init__(self, config: BaseToolConfig = BaseToolConfig()):
        """
        Initializes the BaseTool with an optional description override.

        Args:
            config (BaseToolConfig): Configuration for the tool, including optional title and description overrides.
        """
        self.tool_name = config.title or self.input_schema.model_json_schema()['title']
        self.tool_description = config.description or self.input_schema.model_json_schema()['description']

    def run(self, params: Type[BaseIOSchema]) -> BaseIOSchema:
        """
        Runs the tool with the given parameters. This method should be implemented by subclasses.

        Args:
            params (BaseIOSchema): The input parameters for the tool, adhering to the input schema.

        Returns:
            BaseIOSchema: The output of the tool, adhering to the output schema.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement this method")
