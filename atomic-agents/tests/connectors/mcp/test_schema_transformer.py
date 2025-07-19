import pytest
from typing import Any, Dict, List, Optional

from atomic_agents import BaseIOSchema
from atomic_agents.connectors.mcp import SchemaTransformer


class TestSchemaTransformer:
    def test_string_type_required(self):
        prop_schema = {"type": "string", "description": "A string field"}
        result = SchemaTransformer.json_to_pydantic_field(prop_schema, True)
        assert result[0] == str
        assert result[1].description == "A string field"
        assert result[1].is_required() is True

    def test_number_type_optional(self):
        prop_schema = {"type": "number", "description": "A number field"}
        result = SchemaTransformer.json_to_pydantic_field(prop_schema, False)
        assert result[0] == Optional[float]
        assert result[1].description == "A number field"
        assert result[1].default is None

    def test_integer_type_with_default(self):
        prop_schema = {"type": "integer", "description": "An integer field", "default": 42}
        result = SchemaTransformer.json_to_pydantic_field(prop_schema, False)
        assert result[0] == int
        assert result[1].description == "An integer field"
        assert result[1].default == 42

    def test_boolean_type(self):
        prop_schema = {"type": "boolean", "description": "A boolean field"}
        result = SchemaTransformer.json_to_pydantic_field(prop_schema, True)
        assert result[0] == bool
        assert result[1].description == "A boolean field"
        assert result[1].is_required() is True

    def test_array_type_with_string_items(self):
        prop_schema = {"type": "array", "description": "An array of strings", "items": {"type": "string"}}
        result = SchemaTransformer.json_to_pydantic_field(prop_schema, True)
        assert result[0] == List[str]
        assert result[1].description == "An array of strings"
        assert result[1].is_required() is True

    def test_array_type_with_untyped_items(self):
        prop_schema = {"type": "array", "description": "An array of unknown types", "items": {}}
        result = SchemaTransformer.json_to_pydantic_field(prop_schema, True)
        assert result[0] == List[Any]
        assert result[1].description == "An array of unknown types"
        assert result[1].is_required() is True

    def test_object_type(self):
        prop_schema = {"type": "object", "description": "An object field"}
        result = SchemaTransformer.json_to_pydantic_field(prop_schema, True)
        assert result[0] == Dict[str, Any]
        assert result[1].description == "An object field"
        assert result[1].is_required() is True

    def test_unknown_type(self):
        prop_schema = {"type": "unknown", "description": "An unknown field"}
        result = SchemaTransformer.json_to_pydantic_field(prop_schema, True)
        assert result[0] == Any
        assert result[1].description == "An unknown field"
        assert result[1].is_required() is True

    def test_no_type(self):
        prop_schema = {"description": "A field without type"}
        result = SchemaTransformer.json_to_pydantic_field(prop_schema, True)
        assert result[0] == Any
        assert result[1].description == "A field without type"
        assert result[1].is_required() is True


class TestCreateModelFromSchema:
    def test_basic_model_creation(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "A name"},
                "age": {"type": "integer", "description": "An age"},
            },
            "required": ["name"],
        }
        model = SchemaTransformer.create_model_from_schema(schema, "TestModel", "test_tool")

        # Check the model structure
        assert issubclass(model, BaseIOSchema)
        assert model.__name__ == "TestModel"
        assert "tool_name" in model.model_fields
        assert "name" in model.model_fields
        assert "age" in model.model_fields

        # Test required vs optional fields
        assert model.model_fields["name"].is_required() is True
        assert model.model_fields["age"].is_required() is False

        # Test type annotations
        assert model.model_fields["name"].annotation == str
        assert model.model_fields["age"].annotation == Optional[int]

        # Test docstring
        assert model.__doc__ == "Dynamically generated Pydantic model for TestModel"

    def test_model_with_custom_docstring(self):
        schema = {"type": "object", "properties": {}}
        model = SchemaTransformer.create_model_from_schema(schema, "TestModel", "test_tool", docstring="Custom docstring")
        assert model.__doc__ == "Custom docstring"

    def test_empty_object_schema(self):
        schema = {"type": "object"}
        model = SchemaTransformer.create_model_from_schema(schema, "EmptyModel", "empty_tool")
        assert issubclass(model, BaseIOSchema)
        assert model.__name__ == "EmptyModel"
        assert "tool_name" in model.model_fields
        assert len(model.model_fields) == 1  # Only the tool_name field

    def test_non_object_schema(self, caplog):
        schema = {"type": "string"}
        model = SchemaTransformer.create_model_from_schema(schema, "StringModel", "string_tool")
        assert issubclass(model, BaseIOSchema)
        assert model.__name__ == "StringModel"
        assert "tool_name" in model.model_fields
        assert len(model.model_fields) == 1  # Only the tool_name field
        assert "Schema for StringModel is not a typical object with properties" in caplog.text

    def test_tool_name_field(self):
        schema = {"type": "object", "properties": {}}
        model = SchemaTransformer.create_model_from_schema(schema, "ToolModel", "specific_tool")

        # Test that tool_name is a Literal type with the correct value
        assert "tool_name" in model.model_fields
        tool_instance = model(tool_name="specific_tool")
        assert tool_instance.tool_name == "specific_tool"

        # Test that an invalid tool_name raises an error
        with pytest.raises(ValueError):
            model(tool_name="wrong_tool")
