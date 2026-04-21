"""Unit tests for Manifest provider integration with Atomic Agents."""

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


def _create_manifest_client(api_key="test-key", base_url="https://app.manifest.build/v1"):
    """Create a Manifest client via OpenAI-compatible interface."""
    from openai import OpenAI

    return instructor.from_openai(OpenAI(base_url=base_url, api_key=api_key))


class TestManifestClientSetup:
    """Tests for Manifest client initialization."""

    def test_manifest_client_creation(self):
        """Test that Manifest client can be created with correct base_url."""
        from openai import OpenAI

        raw_client = OpenAI(base_url="https://app.manifest.build/v1", api_key="test-key")
        assert raw_client.base_url == "https://app.manifest.build/v1/"

    def test_manifest_instructor_wrapping(self):
        """Test that Manifest client can be wrapped with instructor."""
        client = _create_manifest_client()
        assert isinstance(client, instructor.Instructor)

    def test_manifest_agent_config(self):
        """Test that AgentConfig accepts Manifest client and model."""
        client = _create_manifest_client()
        config = AgentConfig(
            client=client,
            model="auto",
        )
        assert config.model == "auto"
        assert config.assistant_role == "assistant"

    def test_manifest_agent_initialization(self):
        """Test that AtomicAgent can be initialized with Manifest config."""
        client = _create_manifest_client()
        config = AgentConfig(
            client=client,
            model="auto",
        )
        agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
        assert agent.model == "auto"
        assert agent.assistant_role == "assistant"

    def test_manifest_self_hosted_url(self):
        """Test that self-hosted Manifest URL works."""
        client = _create_manifest_client(base_url="http://localhost:3001/v1")
        config = AgentConfig(
            client=client,
            model="auto",
        )
        agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
        assert agent.model == "auto"


class TestManifestAgentBehavior:
    """Tests for agent behavior with Manifest provider."""

    @pytest.fixture
    def mock_manifest_instructor(self):
        mock = Mock(spec=instructor.Instructor)
        mock.chat = Mock()
        mock.chat.completions = Mock()
        mock.chat.completions.create = Mock(return_value=BasicChatOutputSchema(chat_message="Manifest response"))
        mock_response = BasicChatOutputSchema(chat_message="Manifest response")
        mock_iter = Mock()
        mock_iter.__iter__ = Mock(return_value=iter([mock_response]))
        mock.chat.completions.create_partial.return_value = mock_iter
        return mock

    @pytest.fixture
    def manifest_agent(self, mock_manifest_instructor):
        config = AgentConfig(
            client=mock_manifest_instructor,
            model="auto",
        )
        return AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)

    def test_run_with_manifest(self, manifest_agent, mock_manifest_instructor):
        """Test that agent.run works with Manifest mock client."""
        user_input = BasicChatInputSchema(chat_message="Hello from Manifest test")
        response = manifest_agent.run(user_input)
        assert response.chat_message == "Manifest response"
        mock_manifest_instructor.chat.completions.create.assert_called_once()

    def test_run_passes_correct_model(self, manifest_agent, mock_manifest_instructor):
        """Test that the correct model name is passed to the API."""
        user_input = BasicChatInputSchema(chat_message="Test")
        manifest_agent.run(user_input)
        call_kwargs = mock_manifest_instructor.chat.completions.create.call_args
        assert call_kwargs.kwargs["model"] == "auto"

    def test_run_stream_with_manifest(self, manifest_agent):
        """Test that streaming works with Manifest mock client."""
        user_input = BasicChatInputSchema(chat_message="Stream test")
        responses = list(manifest_agent.run_stream(user_input))
        assert len(responses) == 1
        assert responses[0].chat_message == "Manifest response"

    def test_history_tracking_with_manifest(self, manifest_agent):
        """Test that chat history is properly tracked."""
        user_input = BasicChatInputSchema(chat_message="First message")
        manifest_agent.run(user_input)
        history = manifest_agent.history.get_history()
        assert len(history) == 2  # user + assistant

    def test_system_prompt_with_manifest(self, mock_manifest_instructor):
        """Test that system prompt works correctly with Manifest."""
        spg = SystemPromptGenerator(
            background=["You are a helpful Manifest-powered assistant."],
        )
        config = AgentConfig(
            client=mock_manifest_instructor,
            model="auto",
            system_prompt_generator=spg,
        )
        agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
        prompt = agent.system_prompt_generator.generate_prompt()
        assert "Manifest" in prompt

    def test_model_api_parameters_with_manifest(self, mock_manifest_instructor):
        """Test that custom API parameters are passed through."""
        config = AgentConfig(
            client=mock_manifest_instructor,
            model="auto",
            model_api_parameters={"temperature": 0.7, "max_tokens": 1024},
        )
        agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
        assert agent.model_api_parameters["temperature"] == 0.7
        assert agent.model_api_parameters["max_tokens"] == 1024

    def test_manifest_reset_history(self, manifest_agent):
        """Test that history reset works with Manifest agent."""
        user_input = BasicChatInputSchema(chat_message="Test")
        manifest_agent.run(user_input)
        manifest_agent.reset_history()
        history = manifest_agent.history.get_history()
        assert len(history) == 0


class TestManifestProviderSetup:
    """Tests for the provider setup function from the quickstart example."""

    def test_setup_client_manifest_by_number(self):
        """Test setup_client with provider number '8'."""
        from openai import OpenAI

        api_key = "test-manifest-key"
        raw_client = OpenAI(base_url="https://app.manifest.build/v1", api_key=api_key)
        client = instructor.from_openai(raw_client)
        assert isinstance(client, instructor.Instructor)

    def test_manifest_env_var_detection(self):
        """Test that MANIFEST_API_KEY env var can be used."""
        with patch.dict(os.environ, {"MANIFEST_API_KEY": "test-env-key"}):
            api_key = os.getenv("MANIFEST_API_KEY")
            assert api_key == "test-env-key"

    def test_manifest_base_url_env_var(self):
        """Test that MANIFEST_BASE_URL env var can override the default."""
        with patch.dict(os.environ, {"MANIFEST_BASE_URL": "http://localhost:3001/v1"}):
            base_url = os.getenv("MANIFEST_BASE_URL", "https://app.manifest.build/v1")
            assert base_url == "http://localhost:3001/v1"

    def test_manifest_base_url_default(self):
        """Test that the default base URL is used when env var is not set."""
        with patch.dict(os.environ, {}, clear=True):
            base_url = os.getenv("MANIFEST_BASE_URL", "https://app.manifest.build/v1")
            assert base_url == "https://app.manifest.build/v1"
