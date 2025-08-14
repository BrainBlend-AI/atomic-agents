from typing import Optional, Type, get_args
from abc import ABC, abstractmethod
from pydantic import BaseModel

from atomic_agents.base.base_io_schema import BaseIOSchema


class BaseToolConfig(BaseModel):
    """
    Configuration for a tool.

    Attributes:
        title (Optional[str]): Overrides the default title of the tool.
        description (Optional[str]): Overrides the default description of the tool.
    """

    title: Optional[str] = None
    description: Optional[str] = None


class BaseTool[InputSchema: BaseIOSchema, OutputSchema: BaseIOSchema](ABC):
    """
    Base class for tools within the Atomic Agents framework.

    Tools enable agents to perform specific tasks by providing a standardized interface
    for input and output. Each tool is defined with specific input and output schemas
    that enforce type safety and provide documentation.

    Type Parameters:
        InputSchema: Schema defining the input data, must be a subclass of BaseIOSchema.
        OutputSchema: Schema defining the output data, must be a subclass of BaseIOSchema.

    Attributes:
        config (BaseToolConfig): Configuration for the tool, including optional title and description overrides.
        input_schema (Type[InputSchema]): Schema class defining the input data (derived from generic type parameter).
        output_schema (Type[OutputSchema]): Schema class defining the output data (derived from generic type parameter).
        tool_name (str): The name of the tool, derived from the input schema's title or overridden by the config.
        tool_description (str): Description of the tool, derived from the input schema's description or overridden by the config.
    """

    def __init__(self, config: BaseToolConfig = BaseToolConfig()):
        """
        Initializes the BaseTool with an optional configuration override.

        Args:
            config (BaseToolConfig, optional): Configuration for the tool, including optional title and description overrides.
        """
        self.config = config

    @property
    def input_schema(self) -> Type[InputSchema]:
        """
        Returns the input schema class for the tool.

        Returns:
            Type[InputSchema]: The input schema class.
        """
        if hasattr(self, "__orig_class__"):
            TI, _ = get_args(self.__orig_class__)
        else:
            TI = BaseIOSchema

        return TI

    @property
    def output_schema(self) -> Type[OutputSchema]:
        """
        Returns the output schema class for the tool.

        Returns:
            Type[OutputSchema]: The output schema class.
        """
        if hasattr(self, "__orig_class__"):
            _, TO = get_args(self.__orig_class__)
        else:
            TO = BaseIOSchema

        return TO

    @property
    def tool_name(self) -> str:
        """
        Returns the name of the tool.

        Returns:
            str: The name of the tool.
        """
        return self.config.title or self.input_schema.model_json_schema()["title"]

    @property
    def tool_description(self) -> str:
        """
        Returns the description of the tool.

        Returns:
            str: The description of the tool.
        """
        return self.config.description or self.input_schema.model_json_schema()["description"]

    @abstractmethod
    def run(self, params: InputSchema) -> OutputSchema:
        """
        Executes the tool with the provided parameters.

        Args:
            params (InputSchema): Input parameters adhering to the input schema.

        Returns:
            OutputSchema: Output resulting from executing the tool, adhering to the output schema.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        pass
