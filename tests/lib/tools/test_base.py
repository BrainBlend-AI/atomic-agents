import pytest
from pydantic import BaseModel
from atomic_agents.lib.tools.base import BaseToolConfig, BaseTool
from atomic_agents.agents.base_chat_agent import BaseAgentIO

# Mock classes for testing
class MockInputSchema(BaseAgentIO):
    class Config:
        title = "Mock Input"
        description = "Mock input description"

class MockOutputSchema(BaseAgentIO):
    result: str

class MockTool(BaseTool):
    input_schema = MockInputSchema
    output_schema = MockOutputSchema

    def run(self, params: MockInputSchema) -> MockOutputSchema:
        return MockOutputSchema(result="Mock result")

def test_base_tool_config_creation():
    config = BaseToolConfig()
    assert config.title is None
    assert config.description is None

def test_base_tool_config_with_values():
    config = BaseToolConfig(title="Test Tool", description="Test description")
    assert config.title == "Test Tool"
    assert config.description == "Test description"

def test_base_tool_initialization():
    tool = MockTool()
    assert tool.tool_name == "Mock Input"
    assert tool.tool_description == "Mock input description"

def test_base_tool_with_config():
    config = BaseToolConfig(title="Custom Title", description="Custom description")
    tool = MockTool(config=config)
    assert tool.tool_name == "Custom Title"
    assert tool.tool_description == "Custom description"

def test_base_tool_run_not_implemented():
    class UnimplementedTool(BaseTool):
        input_schema = MockInputSchema
        output_schema = MockOutputSchema

    tool = UnimplementedTool()
    with pytest.raises(NotImplementedError):
        tool.run(MockInputSchema())

def test_mock_tool_run():
    tool = MockTool()
    result = tool.run(MockInputSchema())
    assert isinstance(result, MockOutputSchema)
    assert result.result == "Mock result"

def test_base_tool_input_schema():
    tool = MockTool()
    assert tool.input_schema == MockInputSchema

def test_base_tool_output_schema():
    tool = MockTool()
    assert tool.output_schema == MockOutputSchema

def test_base_tool_inheritance():
    tool = MockTool()
    assert isinstance(tool, BaseTool)

def test_base_tool_config_is_pydantic_model():
    assert issubclass(BaseToolConfig, BaseModel)

def test_base_tool_config_optional_fields():
    config = BaseToolConfig()
    assert hasattr(config, 'title')
    assert hasattr(config, 'description')