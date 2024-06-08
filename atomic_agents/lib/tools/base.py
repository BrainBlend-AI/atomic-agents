from typing import Type, Optional
from pydantic import BaseModel
from dataclasses import dataclass

class BaseToolConfig(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None

class BaseTool:
    """
    Base class for all tools in the Atomic Agents framework.

    Attributes:
        input_schema (Type[BaseModel]): The schema for the input data.
        output_schema (Type[BaseModel]): The schema for the output data.
        tool_name (str): The name of the tool, derived from the input schema's title.
        tool_description (str): The description of the tool, derived from the input schema's description or overridden by the user.
    """

    input_schema: Type[BaseModel]
    output_schema: Type[BaseModel]

    def __init__(self, config: BaseToolConfig = BaseToolConfig()):
        """
        Initializes the BaseTool with an optional description override.

        Args:
            config (BaseToolConfig): Configuration for the tool, including optional title and description overrides.
        """
        self.tool_name = config.title or self.input_schema.Config.title
        self.tool_description = config.description or self.input_schema.Config.description

    def run(self, params: Type[BaseModel]) -> BaseModel:
        """
        Runs the tool with the given parameters. This method should be implemented by subclasses.

        Args:
            params (BaseModel): The input parameters for the tool, adhering to the input schema.

        Returns:
            BaseModel: The output of the tool, adhering to the output schema.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement this method")