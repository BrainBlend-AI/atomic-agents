"""Module for transforming JSON schemas to Pydantic models."""

import logging
from typing import Any, Dict, List, Optional, Type, Tuple, Literal, Union, cast

from pydantic import Field, create_model

from atomic_agents.base.base_io_schema import BaseIOSchema

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
    def _resolve_ref(ref_path: str, root_schema: Dict[str, Any], model_cache: Dict[str, Type]) -> Type:
        """Resolve a $ref to a Pydantic model."""
        # Extract ref name from path like "#/$defs/MyObject" or "#/definitions/ANode"
        ref_name = ref_path.split("/")[-1]

        if ref_name in model_cache:
            return model_cache[ref_name]

        # Look for the referenced schema in $defs or definitions
        defs = root_schema.get("$defs", root_schema.get("definitions", {}))
        if ref_name in defs:
            ref_schema = defs[ref_name]
            # Create model for the referenced schema
            model_name = ref_schema.get("title", ref_name)
            # Avoid infinite recursion by adding placeholder first
            model_cache[ref_name] = Any
            model = SchemaTransformer._create_nested_model(ref_schema, model_name, root_schema, model_cache)
            model_cache[ref_name] = model
            return model

        logger.warning(f"Could not resolve $ref: {ref_path}")
        return Any

    @staticmethod
    def _create_nested_model(
        schema: Dict[str, Any], model_name: str, root_schema: Dict[str, Any], model_cache: Dict[str, Type]
    ) -> Type:
        """Create a nested Pydantic model from a schema."""
        fields = {}
        required_fields = set(schema.get("required", []))
        properties = schema.get("properties", {})

        for prop_name, prop_schema in properties.items():
            is_required = prop_name in required_fields
            fields[prop_name] = SchemaTransformer.json_to_pydantic_field(prop_schema, is_required, root_schema, model_cache)

        return create_model(model_name, **fields)

    @staticmethod
    def json_to_pydantic_field(
        prop_schema: Dict[str, Any],
        required: bool,
        root_schema: Optional[Dict[str, Any]] = None,
        model_cache: Optional[Dict[str, Type]] = None,
    ) -> Tuple[Type, Field]:
        """
        Convert a JSON schema property to a Pydantic field.

        Args:
            prop_schema: JSON schema for the property
            required: Whether the field is required
            root_schema: Full root schema for resolving $refs
            model_cache: Cache for resolved models

        Returns:
            Tuple of (type, Field)
        """
        if root_schema is None:
            root_schema = {}
        if model_cache is None:
            model_cache = {}

        description = prop_schema.get("description")
        default = prop_schema.get("default")
        python_type: Any = Any

        # Handle $ref
        if "$ref" in prop_schema:
            python_type = SchemaTransformer._resolve_ref(prop_schema["$ref"], root_schema, model_cache)
        # Handle oneOf/anyOf (unions)
        elif "oneOf" in prop_schema or "anyOf" in prop_schema:
            union_schemas = prop_schema.get("oneOf", prop_schema.get("anyOf", []))
            if union_schemas:
                union_types = []
                for union_schema in union_schemas:
                    if "$ref" in union_schema:
                        union_types.append(SchemaTransformer._resolve_ref(union_schema["$ref"], root_schema, model_cache))
                    else:
                        # Recursively resolve the union member
                        member_type, _ = SchemaTransformer.json_to_pydantic_field(union_schema, True, root_schema, model_cache)
                        union_types.append(member_type)

                if len(union_types) == 1:
                    python_type = union_types[0]
                else:
                    python_type = Union[tuple(union_types)]
        # Handle regular types
        else:
            json_type = prop_schema.get("type")
            if json_type in JSON_TYPE_MAP:
                python_type = JSON_TYPE_MAP[json_type]

                if json_type == "array":
                    items_schema = prop_schema.get("items", {})
                    if "$ref" in items_schema:
                        item_type = SchemaTransformer._resolve_ref(items_schema["$ref"], root_schema, model_cache)
                    elif "oneOf" in items_schema or "anyOf" in items_schema:
                        # Handle arrays of unions
                        item_type, _ = SchemaTransformer.json_to_pydantic_field(items_schema, True, root_schema, model_cache)
                    elif items_schema.get("type") in JSON_TYPE_MAP:
                        item_type = JSON_TYPE_MAP[items_schema["type"]]
                    else:
                        item_type = Any
                    python_type = List[item_type]

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
        model_cache: Dict[str, Type] = {}

        if properties:
            for prop_name, prop_schema in properties.items():
                is_required = prop_name in required_fields
                fields[prop_name] = SchemaTransformer.json_to_pydantic_field(prop_schema, is_required, schema, model_cache)
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
            __config__={"title": tool_name_literal},
            **fields,
        )

        return model
