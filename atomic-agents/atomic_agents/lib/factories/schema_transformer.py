"""Module for transforming JSON schemas to Pydantic models."""

import logging
from typing import Any, Dict, List, Optional, Type, Tuple, Literal, cast

from pydantic import Field, create_model

from atomic_agents.lib.base.base_io_schema import BaseIOSchema

logger = logging.getLogger(__name__)

# JSON type mapping
JSON_TYPE_MAP = {
    "string": str,
    "number": float,
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
}


class SchemaTransformer:
    """Class for transforming JSON schemas to Pydantic models."""

    @staticmethod
    def json_to_pydantic_field(prop_schema: Dict[str, Any], required: bool) -> Tuple[Type, Field]:
        """
        Convert a JSON schema property to a Pydantic field.

        Args:
            prop_schema: JSON schema for the property
            required: Whether the field is required

        Returns:
            Tuple of (type, Field)
        """
        json_type = prop_schema.get("type")
        description = prop_schema.get("description")
        default = prop_schema.get("default")
        python_type: Any = Any

        if json_type in JSON_TYPE_MAP:
            python_type = JSON_TYPE_MAP[json_type]
            if json_type == "array":
                items_schema = prop_schema.get("items", {})
                item_type_str = items_schema.get("type")
                if item_type_str in JSON_TYPE_MAP:
                    python_type = List[JSON_TYPE_MAP[item_type_str]]
                else:
                    python_type = List[Any]
            elif json_type == "object":
                python_type = Dict[str, Any]

        field_kwargs = {"description": description}
        if required:
            field_kwargs["default"] = ...
        elif default is not None:
            field_kwargs["default"] = default
        else:
            python_type = Optional[python_type]
            field_kwargs["default"] = None

        return (python_type, Field(**field_kwargs))

    @staticmethod
    def create_model_from_schema(
        schema: Dict[str, Any],
        model_name: str,
        tool_name_literal: str,
        docstring: Optional[str] = None,
    ) -> Type[BaseIOSchema]:
        """
        Dynamically create a Pydantic model from a JSON schema.

        Args:
            schema: JSON schema
            model_name: Name for the model
            tool_name_literal: Tool name to use for the Literal type
            docstring: Optional docstring for the model

        Returns:
            Pydantic model class
        """
        fields = {}
        required_fields = set(schema.get("required", []))
        properties = schema.get("properties")

        if properties:
            for prop_name, prop_schema in properties.items():
                is_required = prop_name in required_fields
                fields[prop_name] = SchemaTransformer.json_to_pydantic_field(prop_schema, is_required)
        elif schema.get("type") == "object" and not properties:
            pass
        elif schema:
            logger.warning(
                f"Schema for {model_name} is not a typical object with properties. Fields might be empty beyond tool_name."
            )

        # Create a proper Literal type for tool_name
        tool_name_type = cast(Type[str], Literal[tool_name_literal])  # type: ignore
        fields["tool_name"] = (
            tool_name_type,
            Field(..., description=f"Required identifier for the {tool_name_literal} tool."),
        )

        # Create the model
        model = create_model(
            model_name,
            __base__=BaseIOSchema,
            __doc__=docstring or f"Dynamically generated Pydantic model for {model_name}",
            model_config={"title": tool_name_literal},
            **fields,
        )

        return model
