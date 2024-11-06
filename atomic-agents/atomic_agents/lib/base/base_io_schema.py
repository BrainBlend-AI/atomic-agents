import inspect
from pydantic import BaseModel
from rich.json import JSON


class BaseIOSchema(BaseModel):
    """Base schema for input/output in the Atomic Agents framework."""

    def __str__(self):
        return self.model_dump_json()

    def __rich__(self):
        json_str = self.model_dump_json()
        return JSON(json_str)

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        super().__pydantic_init_subclass__(**kwargs)
        cls._validate_description()

    @classmethod
    def _validate_description(cls):
        description = cls.__doc__

        if not description or not description.strip():
            if cls.__module__ != "instructor.function_calls" and not hasattr(cls, "from_streaming_response"):
                raise ValueError(f"{cls.__name__} must have a non-empty docstring to serve as its description")

    @classmethod
    def model_json_schema(cls, *args, **kwargs):
        schema = super().model_json_schema(*args, **kwargs)
        if "description" not in schema and cls.__doc__:
            schema["description"] = inspect.cleandoc(cls.__doc__)
        if "title" not in schema:
            schema["title"] = cls.__name__
        return schema
