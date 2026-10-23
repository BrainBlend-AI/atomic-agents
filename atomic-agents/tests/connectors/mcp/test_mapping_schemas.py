import asyncio
from unittest.mock import AsyncMock

import pytest
from mcp import ClientSession
from mcp.types import CallToolResult
from pydantic import ValidationError

from atomic_agents.connectors.mcp import MCPFactory, MCPToolDefinition, SchemaTransformer


@pytest.mark.parametrize("definitions_key", ["$defs", "definitions"])
@pytest.mark.parametrize("inline", [False, True], ids=["referenced", "inline"])
@pytest.mark.parametrize("empty_properties", [False, True])
def test_typed_mapping_preserves_values_and_validates_items(definitions_key, inline, empty_properties):
    mapping = {"type": "object", "additionalProperties": {"type": "integer"}}
    if empty_properties:
        mapping["properties"] = {}
    schema = {
        "type": "object",
        "properties": {"counts": mapping if inline else {"$ref": f"#/{definitions_key}/Counts"}},
        "required": ["counts"],
        definitions_key: {"Counts": mapping},
    }
    model = SchemaTransformer.create_model_from_schema(schema, "CountsOutput", "count", is_output_schema=True)
    counts = {"apples": 3, "oranges": 7}
    assert model(counts=counts).model_dump() == {"counts": counts}
    assert model(counts={}).model_dump() == {"counts": {}}
    assert model.model_json_schema()["properties"]["counts"]["additionalProperties"] == {"type": "integer"}
    with pytest.raises(ValidationError):
        model(counts={"apples": "invalid"})


@pytest.mark.parametrize("additional_properties", [None, True, {}])
def test_untyped_referenced_mapping_preserves_arbitrary_values(additional_properties):
    mapping = {"type": "object"}
    if additional_properties is not None:
        mapping["additionalProperties"] = additional_properties
    schema = {
        "type": "object",
        "properties": {"data": {"$ref": "#/$defs/Data"}},
        "required": ["data"],
        "$defs": {"Data": mapping},
    }
    model = SchemaTransformer.create_model_from_schema(schema, "DataOutput", "data", is_output_schema=True)
    data = {"name": "sample", "count": 3, "nested": [False, None, {"value": 7}]}
    assert model(data=data).model_dump() == {"data": data}


@pytest.mark.asyncio
async def test_generated_tool_preserves_mapping_arguments_and_structured_results():
    schema = {
        "type": "object",
        "properties": {"groups": {"$ref": "#/$defs/Groups"}},
        "required": ["groups"],
        "$defs": {
            "Groups": {"type": "object", "additionalProperties": {"type": "array", "items": {"$ref": "#/$defs/Item"}}},
            "Item": {"type": "object", "properties": {"count": {"type": "integer"}}, "required": ["count"]},
        },
    }
    session = AsyncMock(spec=ClientSession)
    session.call_tool.return_value = CallToolResult(content=[], structuredContent={"groups": {"result": [{"count": 7}]}})
    factory = MCPFactory(client_session=session, event_loop=asyncio.get_running_loop())
    tool = factory._create_tool_classes([MCPToolDefinition("group", "Group items", schema, schema)])[0]()
    groups = {"input": [{"count": 3}]}
    params = tool.input_schema(tool_name="group", groups=groups)
    result = await tool.arun(params)

    session.call_tool.assert_awaited_once_with(name="group", arguments={"groups": groups})
    assert result.model_dump() == {"groups": {"result": [{"count": 7}]}}
    with pytest.raises(ValidationError):
        tool.input_schema(tool_name="group", groups={"input": [{"count": "invalid"}]})
    with pytest.raises(ValidationError):
        tool.output_schema(groups={"result": [{}]})
