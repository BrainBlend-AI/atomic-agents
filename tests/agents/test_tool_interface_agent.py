import pytest
from unittest.mock import Mock, patch
from pydantic import Field
import instructor

from atomic_agents.agents.tool_interface_agent import ToolInterfaceAgent, ToolInterfaceAgentConfig
from atomic_agents.lib.tools.base_tool import BaseTool
from atomic_agents.agents.base_agent import BaseIOSchema, BaseAgentOutputSchema


class MockTool(BaseTool):
    class InputSchema(BaseIOSchema):
        """Mock input schema"""

        query: str = Field(..., description="The query to process")

    class OutputSchema(BaseIOSchema):
        """Mock output schema"""

        result: str = Field(..., description="The result of the tool operation")

    input_schema = InputSchema
    output_schema = OutputSchema

    def run(self, params: InputSchema) -> OutputSchema:
        return self.OutputSchema(result=f"Processed: {params.query}")


@pytest.fixture
def mock_tool():
    return MockTool()


@pytest.fixture
def mock_instructor():
    mock = Mock(spec=instructor.Instructor)
    mock.chat.completions.create = Mock()
    return mock


@pytest.fixture
def tool_interface_agent(mock_tool, mock_instructor):
    config = ToolInterfaceAgentConfig(client=mock_instructor, model="gpt-4o-mini", tool_instance=mock_tool)
    return ToolInterfaceAgent(config)


def test_tool_interface_agent_initialization(tool_interface_agent, mock_tool):
    assert tool_interface_agent.tool_instance == mock_tool
    assert tool_interface_agent.input_schema.__name__ == "MockTool"
    assert issubclass(tool_interface_agent.input_schema, BaseIOSchema)
    assert tool_interface_agent.output_schema == BaseAgentOutputSchema


def test_tool_interface_agent_input_schema(tool_interface_agent):
    assert "tool_input" in tool_interface_agent.input_schema.model_fields
    assert tool_interface_agent.input_schema.model_fields["tool_input"].alias == "tool_input_MockTool"


@patch("atomic_agents.agents.base_agent.BaseAgent.get_response")
@patch("atomic_agents.lib.utils.format_tool_message.format_tool_message")
def test_tool_interface_agent_get_response(mock_format_tool_message, mock_get_response, tool_interface_agent):
    mock_tool_input = tool_interface_agent.input_schema(tool_input_MockTool="Test query")
    mock_tool_output = MockTool.OutputSchema(result="Mocked result")
    mock_final_response = Mock()

    mock_get_response.side_effect = [mock_tool_input, mock_final_response]
    tool_interface_agent.tool_instance.run = Mock(return_value=mock_tool_output)
    mock_format_tool_message.return_value = {
        "id": "test_id",
        "type": "function",
        "function": {"name": "MockTool", "arguments": "{}"},
    }

    response = tool_interface_agent.get_response()

    tool_interface_agent.tool_instance.run.assert_called_once_with(mock_tool_input)
    assert mock_get_response.call_count == 2
    assert response == mock_final_response


@patch("atomic_agents.agents.base_agent.BaseAgent.get_response")
@patch("atomic_agents.lib.utils.format_tool_message.format_tool_message")
def test_tool_interface_agent_memory_updates(mock_format_tool_message, mock_get_response, tool_interface_agent):
    mock_input = tool_interface_agent.input_schema(tool_input_MockTool="Test query")
    mock_tool_output = MockTool.OutputSchema(result="Mocked result")
    mock_final_response = BaseAgentOutputSchema(chat_message="Test response")

    mock_get_response.side_effect = [mock_input, mock_final_response]
    tool_interface_agent.tool_instance.run = Mock(return_value=mock_tool_output)
    mock_format_tool_message.return_value = {
        "id": "test_id",
        "type": "function",
        "function": {"name": "MockTool", "arguments": "{}"},
    }

    tool_interface_agent.run(mock_input)

    history = tool_interface_agent.memory.get_history()

    # Check for TOOL CALL message
    assert any("TOOL CALL:" in msg["content"] for msg in history if isinstance(msg["content"], str))

    # Check for TOOL RESPONSE message
    assert any("TOOL RESPONSE:" in msg["content"] for msg in history if isinstance(msg["content"], str))

    # Check if the mocked result is in the memory
    assert any("Mocked result" in msg["content"] for msg in history if isinstance(msg["content"], str))

    # Assert that at least 3 messages were added (TOOL CALL, TOOL RESPONSE, and possibly the final response)
    assert len(history) >= 3
