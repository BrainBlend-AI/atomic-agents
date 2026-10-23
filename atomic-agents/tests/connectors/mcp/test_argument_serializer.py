from copy import deepcopy

import pytest
from jsonschema import Draft202012Validator

from atomic_agents.connectors.mcp.argument_serializer import ArgumentSerializer


@pytest.mark.parametrize("keyword", ["anyOf", "oneOf"])
@pytest.mark.parametrize("kind, expected", [("nullable", {"kind": "nullable", "name": None}), ("plain", {"kind": "plain"})])
def test_structured_union_preserves_null_only_in_the_matching_branch(keyword, kind, expected):
    schema = {
        keyword: [
            {
                "type": "object",
                "properties": {"kind": {"const": "nullable"}, "name": {"type": ["string", "null"]}},
                "required": ["kind"],
            },
            {
                "type": "object",
                "properties": {"kind": {"const": "plain"}, "name": {"type": "string"}},
                "required": ["kind"],
            },
        ]
    }
    arguments = {"kind": kind, "name": None}
    original = deepcopy(arguments)

    result = ArgumentSerializer(schema).serialize(arguments)

    assert result == expected
    Draft202012Validator(schema).validate(result)
    assert arguments == original


def test_recursive_object_reference_filters_each_level_without_mutating_input():
    schema = {
        "type": "object",
        "properties": {"tree": {"$ref": "#/$defs/Node"}},
        "$defs": {
            "Node": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "children": {"type": "array", "items": {"$ref": "#/$defs/Node"}}},
            }
        },
    }
    arguments = {"tree": {"name": None, "children": [{"name": None}, {"name": "leaf"}]}}
    original = deepcopy(arguments)

    result = ArgumentSerializer(schema).serialize(arguments)

    assert result == {"tree": {"children": [{}, {"name": "leaf"}]}}
    Draft202012Validator(schema).validate(result)
    assert arguments == original


@pytest.mark.parametrize("reference", ["#/$defs/Missing", "https://example.invalid/schema.json"])
def test_unresolved_reference_keeps_transformer_any_fallback_without_remote_resolution(reference):
    schema = {"type": "object", "properties": {"value": {"$ref": reference}}}
    assert ArgumentSerializer(schema).serialize({"value": None}) == {"value": None}


@pytest.mark.parametrize("nullable", [True, False])
def test_allof_applies_each_property_null_restriction(nullable):
    schema = {
        "allOf": [
            {"properties": {"name": {"type": ["string", "null"]}}},
            {"properties": {"name": {"type": ["string", "null"] if nullable else "string"}}},
        ]
    }
    result = ArgumentSerializer(schema).serialize({"name": None})
    assert result == ({"name": None} if nullable else {})
    Draft202012Validator(schema).validate(result)


def test_invalid_structured_union_does_not_pick_an_arbitrary_branch():
    schema = {
        "anyOf": [
            {"properties": {"kind": {"const": "first"}, "name": {"type": "string"}}},
            {"properties": {"kind": {"const": "second"}, "name": {"type": ["string", "null"]}}},
        ]
    }
    arguments = {"kind": "unknown", "name": None}
    assert ArgumentSerializer(schema).serialize(arguments) == arguments
