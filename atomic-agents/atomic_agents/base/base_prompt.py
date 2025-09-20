from typing import Optional, Type, get_args, get_origin
from abc import ABC, abstractmethod
from pydantic import BaseModel

from atomic_agents.base.base_io_schema import BaseIOSchema


class BasePromptConfig(BaseModel):
    """
    Configuration for a prompt.

    Attributes:
        title (Optional[str]): Overrides the default title of the prompt.
        description (Optional[str]): Overrides the default description of the prompt.
    """

    title: Optional[str] = None
    description: Optional[str] = None


class BasePrompt[InputSchema: BaseIOSchema, OutputSchema: BaseIOSchema](ABC):
    """
    Base class for prompts within the Atomic Agents framework.

    Prompts enable agents to perform specific tasks by providing a standardized interface
    for input and output. Each prompt is defined with specific input and output schemas
    that enforce type safety and provide documentation.

    Type Parameters:
        InputSchema: Schema defining the input data, must be a subclass of BaseIOSchema.
        OutputSchema: Schema defining the output data, must be a subclass of BaseIOSchema.

    Attributes:
        config (BasePromptConfig): Configuration for the prompt, including optional title and description overrides.
        input_schema (Type[InputSchema]): Schema class defining the input data (derived from generic type parameter).
        output_schema (Type[OutputSchema]): Schema class defining the output data (derived from generic type parameter).
        prompt_name (str): The name of the prompt, derived from the input schema's title or overridden by the config.
        prompt_description (str): Description of the prompt, derived from the input schema's description or overridden by the config.
    """

    def __init__(self, config: BasePromptConfig = BasePromptConfig()):
        """
        Initializes the BasePrompt with an optional configuration override.

        Args:
            config (BasePromptConfig, optional): Configuration for the prompt, including optional title and description overrides.
        """
        self.config = config

    def __init_subclass__(cls, **kwargs):
        """
        Hook called when a class is subclassed.

        Captures generic type parameters during class creation and stores them as class attributes
        to work around the unreliable __orig_class__ attribute in modern Python generic syntax.
        """
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "__orig_bases__"):
            for base in cls.__orig_bases__:
                if get_origin(base) is BasePrompt:
                    args = get_args(base)
                    if len(args) == 2:
                        cls._input_schema_cls = args[0]
                        cls._output_schema_cls = args[1]
                        break

    @property
    def input_schema(self) -> Type[InputSchema]:
        """
        Returns the input schema class for the prompt.

        Returns:
            Type[InputSchema]: The input schema class.
        """
        # Inheritance pattern: MyPrompt(BasePrompt[Schema1, Schema2])
        if hasattr(self.__class__, "_input_schema_cls"):
            return self.__class__._input_schema_cls

        # Dynamic instantiation: MockPrompt[Schema1, Schema2]()
        if hasattr(self, "__orig_class__"):
            TI, _ = get_args(self.__orig_class__)
            return TI

        # No type info available: MockPrompt()
        return BaseIOSchema

    @property
    def output_schema(self) -> Type[OutputSchema]:
        """
        Returns the output schema class for the prompt.

        Returns:
            Type[OutputSchema]: The output schema class.
        """
        # Inheritance pattern: MyPrompt(BasePrompt[Schema1, Schema2])
        if hasattr(self.__class__, "_output_schema_cls"):
            return self.__class__._output_schema_cls

        # Dynamic instantiation: MockPrompt[Schema1, Schema2]()
        if hasattr(self, "__orig_class__"):
            _, TO = get_args(self.__orig_class__)
            return TO

        # No type info available: MockPrompt()
        return BaseIOSchema

    @property
    def prompt_name(self) -> str:
        """
        Returns the name of the prompt.

        Returns:
            str: The name of the prompt.
        """
        return self.config.title or self.input_schema.model_json_schema()["title"]

    @property
    def prompt_description(self) -> str:
        """
        Returns the description of the prompt.

        Returns:
            str: The description of the prompt.
        """
        return self.config.description or self.input_schema.model_json_schema()["description"]

    @abstractmethod
    def generate(self, params: InputSchema) -> OutputSchema:
        """
        Executes the prompt with the provided parameters.

        Args:
            params (InputSchema): Input parameters adhering to the input schema.

        Returns:
            OutputSchema: Output resulting from executing the prompt, adhering to the output schema.

        Raises:
            NotImplementedError: If the method is not implemented by a subclass.
        """
        pass
