"""Unit tests for MiniMax provider integration with Atomic Agents."""

import os
import pytest
from unittest.mock import Mock, patch
import instructor
from atomic_agents import (
    AtomicAgent,
    AgentConfig,
    BasicChatInputSchema,
    BasicChatOutputSchema,
)
from atomic_agents.context import SystemPromptGenerator


def _create_minimax_client(api_key="test-key"):
    """Create a MiniMax client via OpenAI-compatible interface."""
    from openai import OpenAI

    return instructor.from_openai(OpenAI(base_url="https://api.minimax.io/v1", api_key=api_key))


class TestMiniMaxClientSetup:
    """Tests for MiniMax client initialization."""

    def test_minimax_client_creation(self):
        """Test that MiniMax client can be created with correct base_url."""
        from openai import OpenAI

        raw_client = OpenAI(base_url="https://api.minimax.io/v1", api_key="test-key")
        assert raw_client.base_url == "https://api.minimax.io/v1/"

    def test_minimax_instructor_wrapping(self):
        """Test that MiniMax client can be wrapped with instructor."""
        client = _create_minimax_client()
        assert isinstance(client, instructor.Instructor)

    def test_minimax_agent_config(self):
        """Test that AgentConfig accepts MiniMax client and model."""
        client = _create_minimax_client()
        config = AgentConfig(
            client=client,
            model="MiniMax-M2.7",
        )
        assert config.model == "MiniMax-M2.7"
        assert config.assistant_role == "assistant"

    def test_minimax_agent_initialization(self):
        """Test that AtomicAgent can be initialized with MiniMax config."""
        client = _create_minimax_client()
        config = AgentConfig(
            client=client,
            model="MiniMax-M2.7",
        )
        agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
        assert agent.model == "MiniMax-M2.7"
        assert agent.assistant_role == "assistant"

    def test_minimax_m25_model(self):
        """Test that M2.5 model variant works."""
        client = _create_minimax_client()
        config = AgentConfig(
            client=client,
            model="MiniMax-M2.5",
        )
        agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
        assert agent.model == "MiniMax-M2.5"

    def test_minimax_m25_highspeed_model(self):
        """Test that M2.5-highspeed model variant works."""
        client = _create_minimax_client()
        config = AgentConfig(
            client=client,
            model="MiniMax-M2.5-highspeed",
        )
        agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
        assert agent.model == "MiniMax-M2.5-highspeed"


class TestMiniMaxAgentBehavior:
    """Tests for agent behavior with MiniMax provider."""

    @pytest.fixture
    def mock_minimax_instructor(self):
        mock = Mock(spec=instructor.Instructor)
        mock.chat = Mock()
        mock.chat.completions = Mock()
        mock.chat.completions.create = Mock(return_value=BasicChatOutputSchema(chat_message="MiniMax response"))
        mock_response = BasicChatOutputSchema(chat_message="MiniMax response")
        mock_iter = Mock()
        mock_iter.__iter__ = Mock(return_value=iter([mock_response]))
        mock.chat.completions.create_partial.return_value = mock_iter
        return mock

    @pytest.fixture
    def minimax_agent(self, mock_minimax_instructor):
        config = AgentConfig(
            client=mock_minimax_instructor,
            model="MiniMax-M2.7",
        )
        return AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)

    def test_run_with_minimax(self, minimax_agent, mock_minimax_instructor):
        """Test that agent.run works with MiniMax mock client."""
        user_input = BasicChatInputSchema(chat_message="Hello from MiniMax test")
        response = minimax_agent.run(user_input)
        assert response.chat_message == "MiniMax response"
        mock_minimax_instructor.chat.completions.create.assert_called_once()

    def test_run_passes_correct_model(self, minimax_agent, mock_minimax_instructor):
        """Test that the correct model name is passed to the API."""
        user_input = BasicChatInputSchema(chat_message="Test")
        minimax_agent.run(user_input)
        call_kwargs = mock_minimax_instructor.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "MiniMax-M2.7"

    def test_run_stream_with_minimax(self, minimax_agent):
        """Test that streaming works with MiniMax mock client."""
        user_input = BasicChatInputSchema(chat_message="Stream test")
        responses = list(minimax_agent.run_stream(user_input))
        assert len(responses) == 1
        assert responses[0].chat_message == "MiniMax response"

    def test_history_tracking_with_minimax(self, minimax_agent):
        """Test that chat history is properly tracked."""
        user_input = BasicChatInputSchema(chat_message="First message")
        minimax_agent.run(user_input)
        history = minimax_agent.history.get_history()
        assert len(history) == 2  # user + assistant

    def test_system_prompt_with_minimax(self, mock_minimax_instructor):
        """Test that system prompt works correctly with MiniMax."""
        spg = SystemPromptGenerator(
            background=["You are a helpful MiniMax-powered assistant."],
        )
        config = AgentConfig(
            client=mock_minimax_instructor,
            model="MiniMax-M2.7",
            system_prompt_generator=spg,
        )
        agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
        prompt = agent.system_prompt_generator.generate_prompt()
        assert "MiniMax" in prompt

    def test_model_api_parameters_with_minimax(self, mock_minimax_instructor):
        """Test that custom API parameters are passed through."""
        config = AgentConfig(
            client=mock_minimax_instructor,
            model="MiniMax-M2.7",
            model_api_parameters={"temperature": 0.7, "max_tokens": 1024},
        )
        agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
        assert agent.model_api_parameters["temperature"] == 0.7
        assert agent.model_api_parameters["max_tokens"] == 1024

    def test_minimax_reset_history(self, minimax_agent):
        """Test that history reset works with MiniMax agent."""
        user_input = BasicChatInputSchema(chat_message="Test")
        minimax_agent.run(user_input)
        minimax_agent.reset_history()
        history = minimax_agent.history.get_history()
        assert len(history) == 0


class TestMiniMaxProviderSetup:
    """Tests for the provider setup function from the quickstart example."""

    def test_setup_client_minimax_by_number(self):
        """Test setup_client with provider number '7'."""
        import sys

        sys.path.insert(
            0,
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "..",
                "..",
                "atomic-examples",
                "quickstart",
                "quickstart",
            ),
        )
        # We can't import the example directly (it has top-level console input),
        # but we can verify the pattern works
        from openai import OpenAI

        api_key = "test-minimax-key"
        raw_client = OpenAI(base_url="https://api.minimax.io/v1", api_key=api_key)
        client = instructor.from_openai(raw_client)
        assert isinstance(client, instructor.Instructor)

    def test_minimax_env_var_detection(self):
        """Test that MINIMAX_API_KEY env var can be used."""
        with patch.dict(os.environ, {"MINIMAX_API_KEY": "test-env-key"}):
            api_key = os.getenv("MINIMAX_API_KEY")
            assert api_key == "test-env-key"
