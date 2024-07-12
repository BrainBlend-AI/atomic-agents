import pytest
from unittest.mock import Mock, patch
from pydantic import Field
from atomic_agents.agents.tool_interface_agent import ToolInterfaceAgent, ToolInterfaceAgentConfig, ToolInputModel
from atomic_agents.agents.base_agent import BaseAgentIO, BaseAgentOutputSchema
from atomic_agents.lib.tools.base import BaseTool
from atomic_agents.lib.components.system_prompt_generator import SystemPromptGenerator, SystemPromptInfo
from atomic_agents.lib.components.agent_memory import AgentMemory
import instructor

class MockToolInputSchema(BaseAgentIO):
    query: str = Field(..., description="Test query")

    class Config:
        title = "Mock Tool Input"
        description = "Mock tool input description"

class MockToolOutputSchema(BaseAgentIO):
    result: str

class MockTool(BaseTool):
    input_schema = MockToolInputSchema
    output_schema = MockToolOutputSchema

    def run(self, params: MockToolInputSchema) -> MockToolOutputSchema:
        return MockToolOutputSchema(result=f"Processed: {params.query}")

@pytest.fixture
def mock_instructor():
    mock = Mock(spec=instructor.Instructor)
    mock.chat.completions.create = Mock()
    return mock

@pytest.fixture
def mock_memory():
    mock = Mock(spec=AgentMemory)
    mock.get_history.return_value = []  # Return an empty list instead of a Mock object
    return mock

@pytest.fixture
def mock_tool():
    return MockTool()

@pytest.fixture
def tool_interface_agent_config(mock_instructor, mock_memory, mock_tool):
    return ToolInterfaceAgentConfig(
        client=mock_instructor,
        model="gpt-3.5-turbo",
        memory=mock_memory,
        tool_instance=mock_tool,
        return_raw_output=False
    )

@pytest.fixture
def tool_interface_agent(tool_interface_agent_config):
    return ToolInterfaceAgent(tool_interface_agent_config)

def test_tool_interface_agent_initialization(tool_interface_agent, mock_tool):
    assert isinstance(tool_interface_agent.tool_instance, BaseTool)
    assert tool_interface_agent.return_raw_output is False
    assert tool_interface_agent.tool_instance == mock_tool

def test_tool_interface_agent_input_schema(tool_interface_agent):
    assert issubclass(tool_interface_agent.input_schema, ToolInputModel)
    assert "tool_input" in tool_interface_agent.input_schema.model_fields

def test_tool_interface_agent_output_schema(tool_interface_agent):
    assert tool_interface_agent.output_schema is not None

def test_tool_interface_agent_system_prompt_generator(tool_interface_agent):
    assert isinstance(tool_interface_agent.system_prompt_generator, SystemPromptGenerator)
    assert isinstance(tool_interface_agent.system_prompt_generator.system_prompt_info, SystemPromptInfo)

def test_tool_interface_agent_with_raw_output(mock_instructor, mock_memory, mock_tool):
    config = ToolInterfaceAgentConfig(
        client=mock_instructor,
        model="gpt-3.5-turbo",
        memory=mock_memory,
        tool_instance=mock_tool,
        return_raw_output=True
    )
    agent = ToolInterfaceAgent(config)
    assert agent.return_raw_output is True
    assert agent.output_schema == mock_tool.output_schema

# @patch('atomic_agents.agents.tool_interface_agent.ToolInterfaceAgent.get_response')
# def test_get_and_handle_response_raw_output(mock_get_response, tool_interface_agent):
#     tool_interface_agent.return_raw_output = True
#     mock_tool_input = MockToolInputSchema(query="test query")
#     mock_tool_output = MockToolOutputSchema(result="Processed: test query")
    
#     mock_get_response.return_value = mock_tool_input
#     tool_interface_agent.tool_instance.run = Mock(return_value=mock_tool_output)
    
#     result = tool_interface_agent._get_and_handle_response()
    
#     assert result == mock_tool_output
#     tool_interface_agent.tool_instance.run.assert_called_once_with(mock_tool_input)

# @patch('atomic_agents.agents.tool_interface_agent.ToolInterfaceAgent.get_response')
# def test_get_and_handle_response_processed_output(mock_get_response, tool_interface_agent):
#     mock_tool_input = MockToolInputSchema(query="test query")
#     mock_tool_output = MockToolOutputSchema(result="Processed: test query")
#     mock_processed_response = BaseAgentIO()
    
#     mock_get_response.side_effect = [mock_tool_input, mock_processed_response]
#     tool_interface_agent.tool_instance.run = Mock(return_value=mock_tool_output)
    
#     result = tool_interface_agent._get_and_handle_response()
    
#     assert result == mock_processed_response
#     tool_interface_agent.tool_instance.run.assert_called_once_with(mock_tool_input)
#     assert mock_get_response.call_count == 2

from pydantic import Field

from unittest.mock import patch

@patch('atomic_agents.agents.tool_interface_agent.ToolInterfaceAgent.get_response')
def test_tool_interface_agent_run(mock_get_response, tool_interface_agent):
    # Inspect the input schema
    print(f"Input schema fields: {tool_interface_agent.input_schema.model_fields}")

    # Create a mock input that matches the schema structure
    mock_input_data = {}
    for field_name, field in tool_interface_agent.input_schema.model_fields.items():
        if field.alias:
            field_name = field.alias
        if isinstance(field.annotation, type) and issubclass(field.annotation, str):
            mock_input_data[field_name] = "Test input"
        elif isinstance(field.annotation, type) and issubclass(field.annotation, dict):
            mock_input_data[field_name] = {"key": "value"}
        else:
            mock_input_data[field_name] = None

    print(f"Mock input data: {mock_input_data}")

    try:
        mock_input = tool_interface_agent.input_schema(**mock_input_data)
    except Exception as e:
        print(f"Error creating mock input: {e}")
        raise

    # Mock the get_response method to return a BaseAgentOutputSchema
    mock_output = BaseAgentOutputSchema(chat_message="Mocked response")
    mock_get_response.return_value = mock_output

    result = tool_interface_agent.run(mock_input)

    assert isinstance(result, BaseAgentOutputSchema)
    assert result.chat_message == "Mocked response"

    # Verify that get_response was called
    mock_get_response.assert_called_once()

if __name__ == '__main__':
    pytest.main()