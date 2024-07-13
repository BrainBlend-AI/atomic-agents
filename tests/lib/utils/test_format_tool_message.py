import uuid
from pydantic import BaseModel
from atomic_agents.lib.utils.format_tool_message import format_tool_message

# Mock classes for testing
class MockToolCall(BaseModel):
    param1: str
    param2: int

    class Config:
        title = "MockTool"

def test_format_tool_message_with_provided_tool_id():
    tool_call = MockToolCall(param1="test", param2=42)
    tool_id = "test-tool-id"
    
    result = format_tool_message(tool_call, tool_id)
    
    assert result == {
        "id": "test-tool-id",
        "type": "function",
        "function": {
            "name": "MockTool",
            "arguments": '{"param1": "test", "param2": 42}'
        }
    }

def test_format_tool_message_without_tool_id():
    tool_call = MockToolCall(param1="test", param2=42)
    
    result = format_tool_message(tool_call)
    
    assert isinstance(result["id"], str)
    assert len(result["id"]) == 36  # UUID length
    assert result["type"] == "function"
    assert result["function"]["name"] == "MockTool"
    assert result["function"]["arguments"] == '{"param1": "test", "param2": 42}'

def test_format_tool_message_with_different_tool():
    class AnotherToolCall(BaseModel):
        field1: bool
        field2: float

        class Config:
            title = "AnotherTool"

    tool_call = AnotherToolCall(field1=True, field2=3.14)
    
    result = format_tool_message(tool_call)
    
    assert result["type"] == "function"
    assert result["function"]["name"] == "AnotherTool"
    assert result["function"]["arguments"] == '{"field1": true, "field2": 3.14}'

def test_format_tool_message_id_is_valid_uuid():
    tool_call = MockToolCall(param1="test", param2=42)
    
    result = format_tool_message(tool_call)
    
    try:
        uuid.UUID(result["id"])
    except ValueError:
        pytest.fail("The generated tool_id is not a valid UUID")

def test_format_tool_message_consistent_output():
    tool_call = MockToolCall(param1="test", param2=42)
    tool_id = "fixed-id"
    
    result1 = format_tool_message(tool_call, tool_id)
    result2 = format_tool_message(tool_call, tool_id)
    
    assert result1 == result2

def test_format_tool_message_with_complex_model():
    class ComplexToolCall(BaseModel):
        nested: dict
        list_field: list

        class Config:
            title = "ComplexTool"

    tool_call = ComplexToolCall(
        nested={"key": "value"},
        list_field=[1, 2, 3]
    )
    
    result = format_tool_message(tool_call)
    
    assert result["function"]["name"] == "ComplexTool"
    assert result["function"]["arguments"] == '{"nested": {"key": "value"}, "list_field": [1, 2, 3]}'