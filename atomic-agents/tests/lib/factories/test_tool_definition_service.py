import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from atomic_agents.lib.factories.tool_definition_service import (
    ToolDefinitionService,
    MCPToolDefinition,
)


class MockAsyncContextManager:
    def __init__(self, return_value=None):
        self.return_value = return_value
        self.enter_called = False
        self.exit_called = False

    async def __aenter__(self):
        self.enter_called = True
        return self.return_value

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.exit_called = True
        return False


@pytest.fixture
def mock_client_session():
    mock_session = AsyncMock()

    # Setup mock responses
    mock_tool = MagicMock()
    mock_tool.name = "TestTool"
    mock_tool.description = "Test tool description"
    mock_tool.inputSchema = {
        "type": "object",
        "properties": {"param1": {"type": "string", "description": "A string parameter"}},
        "required": ["param1"],
    }

    mock_response = MagicMock()
    mock_response.tools = [mock_tool]

    mock_session.list_tools.return_value = mock_response

    # Setup tool result
    mock_tool_result = MagicMock()
    mock_tool_result.content = "Tool result"
    mock_session.call_tool.return_value = mock_tool_result

    return mock_session


class TestToolDefinitionService:
    def test_multiple_transports_raises_error(self):
        """Test that specifying multiple transport types raises an error."""
        with pytest.raises(ValueError, match="Only one of.*can be True"):
            ToolDefinitionService("http://example.com", use_stdio=True, use_streamable_http=True)

    def test_streamable_http_unavailable_raises_error(self, monkeypatch):
        """Test that requesting streamable HTTP when unavailable raises an error."""
        import atomic_agents.lib.factories.tool_definition_service as tds
        # Mock HAS_STREAMABLE_HTTP to False
        monkeypatch.setattr(tds, 'HAS_STREAMABLE_HTTP', False)
        with pytest.raises(ValueError, match="StreamableHTTP transport requested but.*is not available"):
            ToolDefinitionService("http://example.com", use_streamable_http=True)

    @pytest.mark.asyncio
    @patch("atomic_agents.lib.factories.tool_definition_service.sse_client")
    @patch("atomic_agents.lib.factories.tool_definition_service.ClientSession")
    async def test_fetch_via_sse(self, mock_client_session_cls, mock_sse_client, mock_client_session):
        # Setup
        mock_transport = MockAsyncContextManager(return_value=(AsyncMock(), AsyncMock()))
        mock_sse_client.return_value = mock_transport

        mock_session = MockAsyncContextManager(return_value=mock_client_session)
        mock_client_session_cls.return_value = mock_session

        # Create service
        service = ToolDefinitionService("http://test-endpoint")

        # Mock the fetch_definitions_from_session to return directly
        original_method = service.fetch_definitions_from_session
        service.fetch_definitions_from_session = AsyncMock(
            return_value=[
                MCPToolDefinition(
                    name="MockTool",
                    description="Mock tool for testing",
                    input_schema={"type": "object", "properties": {"param": {"type": "string"}}},
                )
            ]
        )

        # Execute
        result = await service.fetch_definitions()

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], MCPToolDefinition)
        assert result[0].name == "MockTool"
        assert result[0].description == "Mock tool for testing"

        # Restore the original method
        service.fetch_definitions_from_session = original_method

    @pytest.mark.asyncio
    async def test_fetch_via_stdio(self):
        # Create service
        service = ToolDefinitionService("command arg1 arg2", use_stdio=True)

        # Mock the fetch_definitions_from_session method
        service.fetch_definitions_from_session = AsyncMock(
            return_value=[
                MCPToolDefinition(
                    name="MockTool",
                    description="Mock tool for testing",
                    input_schema={"type": "object", "properties": {"param": {"type": "string"}}},
                )
            ]
        )

        # Patch the stdio_client to avoid actual subprocess execution
        with patch("atomic_agents.lib.factories.tool_definition_service.stdio_client") as mock_stdio:
            mock_transport = MockAsyncContextManager(return_value=(AsyncMock(), AsyncMock()))
            mock_stdio.return_value = mock_transport

            with patch("atomic_agents.lib.factories.tool_definition_service.ClientSession") as mock_session_cls:
                mock_session = MockAsyncContextManager(return_value=AsyncMock())
                mock_session_cls.return_value = mock_session

                # Execute
                result = await service.fetch_definitions()

                # Verify
                assert len(result) == 1
                assert result[0].name == "MockTool"

    @pytest.mark.asyncio
    async def test_fetch_via_streamable_http(self, monkeypatch):
        """Test fetching tool definitions via streamable HTTP transport."""
        import atomic_agents.lib.factories.tool_definition_service as tds
        
        # Mock streamable HTTP support
        monkeypatch.setattr(tds, 'HAS_STREAMABLE_HTTP', True)
        
        def mock_streamable_http_client(endpoint, headers=None):
            return MockAsyncContextManager(return_value=(AsyncMock(), AsyncMock()))
        
        monkeypatch.setattr(tds, 'streamable_http_client', mock_streamable_http_client)
        
        # Create service with streamable HTTP
        service = ToolDefinitionService(
            "http://test-endpoint", 
            use_streamable_http=True,
            streamable_http_headers={"Authorization": "Bearer token"}
        )

        # Mock the fetch_definitions_from_session method
        service.fetch_definitions_from_session = AsyncMock(
            return_value=[
                MCPToolDefinition(
                    name="StreamableTool",
                    description="Tool via streamable HTTP",
                    input_schema={"type": "object", "properties": {"param": {"type": "string"}}},
                )
            ]
        )

        with patch("atomic_agents.lib.factories.tool_definition_service.ClientSession") as mock_session_cls:
            mock_session = MockAsyncContextManager(return_value=AsyncMock())
            mock_session_cls.return_value = mock_session

            # Execute
            result = await service.fetch_definitions()

            # Verify
            assert len(result) == 1
            assert result[0].name == "StreamableTool"
            assert result[0].description == "Tool via streamable HTTP"

    @pytest.mark.asyncio
    async def test_stdio_empty_command(self):
        # Create service with empty command
        service = ToolDefinitionService("", use_stdio=True)

        # Test that ValueError is raised for empty command
        with pytest.raises(ValueError, match="Endpoint is required"):
            await service.fetch_definitions()

    @pytest.mark.asyncio
    async def test_fetch_definitions_from_session(self, mock_client_session):
        # Execute using the static method
        result = await ToolDefinitionService.fetch_definitions_from_session(mock_client_session)

        # Verify
        assert len(result) == 1
        assert isinstance(result[0], MCPToolDefinition)
        assert result[0].name == "TestTool"

        # Verify session initialization
        mock_client_session.initialize.assert_called_once()
        mock_client_session.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_session_exception(self):
        mock_session = AsyncMock()
        mock_session.initialize.side_effect = Exception("Session error")

        with pytest.raises(Exception, match="Session error"):
            await ToolDefinitionService.fetch_definitions_from_session(mock_session)

    @pytest.mark.asyncio
    async def test_null_input_schema(self, mock_client_session):
        # Create a tool with null inputSchema
        mock_tool = MagicMock()
        mock_tool.name = "NullSchemaTool"
        mock_tool.description = "Tool with null schema"
        mock_tool.inputSchema = None

        mock_response = MagicMock()
        mock_response.tools = [mock_tool]
        mock_client_session.list_tools.return_value = mock_response

        # Execute
        result = await ToolDefinitionService.fetch_definitions_from_session(mock_client_session)

        # Verify default empty schema is created
        assert len(result) == 1
        assert result[0].name == "NullSchemaTool"
        assert result[0].input_schema == {"type": "object", "properties": {}}

    @pytest.mark.asyncio
    async def test_stdio_command_parts_empty(self):
        svc = ToolDefinitionService("   ", use_stdio=True)
        with pytest.raises(
            RuntimeError, match="Unexpected error during tool definition fetching: STDIO command string cannot be empty"
        ):
            await svc.fetch_definitions()

    @pytest.mark.asyncio
    async def test_sse_connection_error(self):
        with patch("atomic_agents.lib.factories.tool_definition_service.sse_client", side_effect=ConnectionError):
            svc = ToolDefinitionService("http://host")
            with pytest.raises(ConnectionError):
                await svc.fetch_definitions()

    @pytest.mark.asyncio
    async def test_generic_error_wrapped(self):
        with patch("atomic_agents.lib.factories.tool_definition_service.sse_client", side_effect=OSError("BOOM")):
            svc = ToolDefinitionService("http://host")
            with pytest.raises(RuntimeError):
                await svc.fetch_definitions()


# Helper class for no-tools test
class _NoToolsResponse:
    """Response object that simulates an empty tools list"""

    tools = []


@pytest.mark.asyncio
async def test_fetch_definitions_from_session_no_tools(caplog):
    """Test handling of empty tools list from session"""
    sess = AsyncMock()
    sess.initialize = AsyncMock()
    sess.list_tools = AsyncMock(return_value=_NoToolsResponse())

    result = await ToolDefinitionService.fetch_definitions_from_session(sess)
    assert result == []
    assert "No tool definitions found" in caplog.text
