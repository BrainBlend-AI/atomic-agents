import pytest
from unittest.mock import Mock, call, patch
from pydantic import BaseModel
import instructor
from atomic_agents import (
    BaseIOSchema,
    AtomicAgent,
    AgentConfig,
    BasicChatInputSchema,
    BasicChatOutputSchema,
)
from atomic_agents.context import ChatHistory, SystemPromptGenerator, BaseDynamicContextProvider
from instructor.dsl.partial import PartialBase


@pytest.fixture
def mock_instructor():
    mock = Mock(spec=instructor.Instructor)
    # Set up the nested mock structure
    mock.chat = Mock()
    mock.chat.completions = Mock()
    mock.chat.completions.create = Mock(return_value=BasicChatOutputSchema(chat_message="Test output"))

    # Make create_partial return an iterable
    mock_response = BasicChatOutputSchema(chat_message="Test output")
    mock_iter = Mock()
    mock_iter.__iter__ = Mock(return_value=iter([mock_response]))
    mock.chat.completions.create_partial.return_value = mock_iter

    return mock


@pytest.fixture
def mock_instructor_async():
    # Changed spec from instructor.Instructor to instructor.client.AsyncInstructor
    mock = Mock(spec=instructor.client.AsyncInstructor)

    # Configure chat.completions structure
    mock.chat = Mock()
    mock.chat.completions = Mock()

    # Make create method awaitable by using an async function
    async def mock_create(*args, **kwargs):
        return BasicChatOutputSchema(chat_message="Test output")

    mock.chat.completions.create = mock_create

    # Mock the create_partial method to return an async generator
    async def mock_create_partial(*args, **kwargs):
        yield BasicChatOutputSchema(chat_message="Test output")

    mock.chat.completions.create_partial = mock_create_partial

    return mock


@pytest.fixture
def mock_history():
    mock = Mock(spec=ChatHistory)
    mock.get_history.return_value = []
    mock.add_message = Mock()
    mock.copy = Mock(return_value=Mock(spec=ChatHistory))
    mock.initialize_turn = Mock()
    return mock


@pytest.fixture
def mock_system_prompt_generator():
    mock = Mock(spec=SystemPromptGenerator)
    mock.generate_prompt.return_value = "Mocked system prompt"
    mock.context_providers = {}
    return mock


@pytest.fixture
def agent_config(mock_instructor, mock_history, mock_system_prompt_generator):
    return AgentConfig(
        client=mock_instructor,
        model="gpt-5-mini",
        history=mock_history,
        system_prompt_generator=mock_system_prompt_generator,
    )


@pytest.fixture
def agent(agent_config):
    return AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](agent_config)


@pytest.fixture
def agent_config_async(mock_instructor_async, mock_history, mock_system_prompt_generator):
    return AgentConfig(
        client=mock_instructor_async,
        model="gpt-5-mini",
        history=mock_history,
        system_prompt_generator=mock_system_prompt_generator,
    )


@pytest.fixture
def agent_async(agent_config_async):
    return AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](agent_config_async)


def test_initialization(agent, mock_instructor, mock_history, mock_system_prompt_generator):
    assert agent.client == mock_instructor
    assert agent.model == "gpt-5-mini"
    assert agent.history == mock_history
    assert agent.system_prompt_generator == mock_system_prompt_generator
    assert "max_tokens" not in agent.model_api_parameters


# model_api_parameters should have priority over other settings
def test_initialization_temperature_priority(mock_instructor, mock_history, mock_system_prompt_generator):
    config = AgentConfig(
        client=mock_instructor,
        model="gpt-5-mini",
        history=mock_history,
        system_prompt_generator=mock_system_prompt_generator,
        model_api_parameters={"temperature": 1.0},
    )
    agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
    assert agent.model_api_parameters["temperature"] == 1.0


def test_initialization_without_temperature(mock_instructor, mock_history, mock_system_prompt_generator):
    config = AgentConfig(
        client=mock_instructor,
        model="gpt-5-mini",
        history=mock_history,
        system_prompt_generator=mock_system_prompt_generator,
        model_api_parameters={"temperature": 0.5},
    )
    agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
    assert agent.model_api_parameters["temperature"] == 0.5


def test_initialization_without_max_tokens(mock_instructor, mock_history, mock_system_prompt_generator):
    config = AgentConfig(
        client=mock_instructor,
        model="gpt-5-mini",
        history=mock_history,
        system_prompt_generator=mock_system_prompt_generator,
        model_api_parameters={"max_tokens": 1024},
    )
    agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
    assert agent.model_api_parameters["max_tokens"] == 1024


def test_initialization_system_role_equals_developer(mock_instructor, mock_history, mock_system_prompt_generator):
    config = AgentConfig(
        client=mock_instructor,
        model="gpt-5-mini",
        history=mock_history,
        system_prompt_generator=mock_system_prompt_generator,
        system_role="developer",
        model_api_parameters={},  # No temperature specified
    )
    agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
    _ = agent._prepare_messages()
    assert isinstance(agent.messages, list) and agent.messages[0]["role"] == "developer"


def test_initialization_system_role_equals_None(mock_instructor, mock_history, mock_system_prompt_generator):
    config = AgentConfig(
        client=mock_instructor,
        model="gpt-5-mini",
        history=mock_history,
        system_prompt_generator=mock_system_prompt_generator,
        system_role=None,
        model_api_parameters={},  # No temperature specified
    )
    agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
    _ = agent._prepare_messages()
    assert isinstance(agent.messages, list) and len(agent.messages) == 0


def test_reset_history(agent, mock_history):
    initial_history = agent.initial_history
    agent.reset_history()
    assert agent.history != initial_history
    mock_history.copy.assert_called_once()


def test_get_context_provider(agent, mock_system_prompt_generator):
    mock_provider = Mock(spec=BaseDynamicContextProvider)
    mock_system_prompt_generator.context_providers = {"test_provider": mock_provider}

    result = agent.get_context_provider("test_provider")
    assert result == mock_provider

    with pytest.raises(KeyError):
        agent.get_context_provider("non_existent_provider")


def test_register_context_provider(agent, mock_system_prompt_generator):
    mock_provider = Mock(spec=BaseDynamicContextProvider)
    agent.register_context_provider("new_provider", mock_provider)

    assert "new_provider" in mock_system_prompt_generator.context_providers
    assert mock_system_prompt_generator.context_providers["new_provider"] == mock_provider


def test_unregister_context_provider(agent, mock_system_prompt_generator):
    mock_provider = Mock(spec=BaseDynamicContextProvider)
    mock_system_prompt_generator.context_providers = {"test_provider": mock_provider}

    agent.unregister_context_provider("test_provider")
    assert "test_provider" not in mock_system_prompt_generator.context_providers

    with pytest.raises(KeyError):
        agent.unregister_context_provider("non_existent_provider")


def test_no_type_parameters(mock_instructor):
    custom_config = AgentConfig(
        client=mock_instructor,
        model="gpt-5-mini",
    )

    custom_agent = AtomicAgent(custom_config)

    assert custom_agent.input_schema == BasicChatInputSchema
    assert custom_agent.output_schema == BasicChatOutputSchema


def test_custom_input_output_schemas(mock_instructor):
    class CustomInputSchema(BaseModel):
        custom_field: str

    class CustomOutputSchema(BaseModel):
        result: str

    custom_config = AgentConfig(
        client=mock_instructor,
        model="gpt-5-mini",
    )

    custom_agent = AtomicAgent[CustomInputSchema, CustomOutputSchema](custom_config)

    assert custom_agent.input_schema == CustomInputSchema
    assert custom_agent.output_schema == CustomOutputSchema


def test_subclass_with_custom_constructor(mock_instructor):
    """Test that generic types are preserved in subclasses with custom constructors."""

    class CustomInputSchema(BaseModel):
        custom_field: str

    class CustomOutputSchema(BaseModel):
        result: str

    class MyAgent(AtomicAgent[CustomInputSchema, CustomOutputSchema]):
        def __init__(self, extra_param: str):
            self.extra_param = extra_param
            config = AgentConfig(
                client=mock_instructor,
                model="gpt-5-mini",
            )
            super().__init__(config)

    agent = MyAgent("test_value")

    # These would fail without the __init_subclass__ fix
    assert agent.input_schema == CustomInputSchema
    assert agent.output_schema == CustomOutputSchema
    assert agent.extra_param == "test_value"


def test_base_agent_io_str_and_rich():
    class TestIO(BaseIOSchema):
        """TestIO docstring"""

        field: str

    test_io = TestIO(field="test")
    assert str(test_io) == '{"field":"test"}'
    assert test_io.__rich__() is not None  # Just check if it returns something, as we can't easily compare Rich objects


def test_base_io_schema_empty_docstring():
    with pytest.raises(ValueError, match="must have a non-empty docstring"):

        class EmptyDocStringSchema(BaseIOSchema):
            """"""

            pass


def test_base_io_schema_model_json_schema_no_description():
    class TestSchema(BaseIOSchema):
        """Test schema docstring."""

        field: str

    # Mock the superclass model_json_schema to return a schema without a description
    with patch("pydantic.BaseModel.model_json_schema", return_value={}):
        schema = TestSchema.model_json_schema()

    assert "description" in schema
    assert schema["description"] == "Test schema docstring."


def test_run(agent, mock_history):
    # Use the agent fixture that's already configured correctly
    mock_input = BasicChatInputSchema(chat_message="Test input")

    result = agent.run(mock_input)

    # Assertions
    assert result.chat_message == "Test output"
    assert agent.current_user_input == mock_input

    mock_history.add_message.assert_has_calls([call("user", mock_input), call("assistant", result)])


def test_messages_sync_after_run(mock_instructor, mock_system_prompt_generator):
    """
    Test that agent.messages includes the assistant response after run() completes.
    
    Regression test for GitHub issue #194:
    https://github.com/BrainBlend-AI/atomic-agents/issues/194
    
    The issue was that agent.messages only contained the system prompt and user message
    after run(), while agent.history.get_history() correctly included the assistant response.
    """
    # Use real ChatHistory instead of mock to verify actual message synchronization
    real_history = ChatHistory()
    
    config = AgentConfig(
        client=mock_instructor,
        model="gpt-5-mini",
        history=real_history,
        system_prompt_generator=mock_system_prompt_generator,
    )
    agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)
    
    mock_input = BasicChatInputSchema(chat_message="Test input")
    
    result = agent.run(mock_input)
    
    # Verify agent.messages is in sync with history.get_history()
    history_messages = agent.history.get_history()
    
    # agent.messages should contain: system prompt + history (user + assistant)
    assert len(agent.messages) == 3, f"Expected 3 messages (system + user + assistant), got {len(agent.messages)}"
    
    # First message should be the system prompt
    assert agent.messages[0]["role"] == "system"
    
    # Second message should be the user input
    assert agent.messages[1]["role"] == "user"
    
    # Third message should be the assistant response (the key fix for issue #194)
    assert agent.messages[2]["role"] == "assistant"
    
    # Verify consistency: agent.messages[-2:] should match history.get_history()
    assert len(history_messages) == 2, f"Expected 2 history messages, got {len(history_messages)}"
    assert agent.messages[1:] == history_messages


def test_run_stream(mock_instructor, mock_history):
    # Create a AgentConfig with system_role set to None
    config = AgentConfig(
        client=mock_instructor,
        model="gpt-5-mini",
        history=mock_history,
        system_prompt_generator=None,  # No system prompt generator
    )
    agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)

    mock_input = BasicChatInputSchema(chat_message="Test input")
    mock_output = BasicChatOutputSchema(chat_message="Test output")

    for result in agent.run_stream(mock_input):
        pass

    assert result == mock_output
    assert agent.current_user_input == mock_input

    mock_history.add_message.assert_has_calls([call("user", mock_input), call("assistant", mock_output)])


@pytest.mark.asyncio
async def test_run_async(agent_async, mock_history):
    # Create a mock input
    mock_input = BasicChatInputSchema(chat_message="Test input")
    mock_output = BasicChatOutputSchema(chat_message="Test output")

    # Get response from run_async method
    response = await agent_async.run_async(mock_input)

    # Assertions
    assert response == mock_output
    assert agent_async.current_user_input == mock_input
    mock_history.add_message.assert_has_calls([call("user", mock_input), call("assistant", mock_output)])


@pytest.mark.asyncio
async def test_run_async_stream(agent_async, mock_history):
    # Create a mock input
    mock_input = BasicChatInputSchema(chat_message="Test input")
    mock_output = BasicChatOutputSchema(chat_message="Test output")

    responses = []
    # Get response from run_async_stream method
    async for response in agent_async.run_async_stream(mock_input):
        responses.append(response)

    # Assertions
    assert len(responses) == 1
    assert responses[0] == mock_output
    assert agent_async.current_user_input == mock_input

    # Verify that both user input and assistant response were added to history
    mock_history.add_message.assert_any_call("user", mock_input)

    # Create the expected full response content to check
    full_response_content = agent_async.output_schema(**responses[0].model_dump())
    mock_history.add_message.assert_any_call("assistant", full_response_content)


def test_model_from_chunks_patched():
    class TestPartialModel(PartialBase):
        @classmethod
        def get_partial_model(cls):
            class PartialModel(BaseModel):
                field: str

            return PartialModel

    chunks = ['{"field": "hel', 'lo"}']
    expected_values = ["hel", "hello"]

    generator = TestPartialModel.model_from_chunks(chunks)
    results = [result.field for result in generator]

    assert results == expected_values


@pytest.mark.asyncio
async def test_model_from_chunks_async_patched():
    class TestPartialModel(PartialBase):
        @classmethod
        def get_partial_model(cls):
            class PartialModel(BaseModel):
                field: str

            return PartialModel

    async def async_gen():
        yield '{"field": "hel'
        yield 'lo"}'

    expected_values = ["hel", "hello"]

    generator = TestPartialModel.model_from_chunks_async(async_gen())
    results = []
    async for result in generator:
        results.append(result.field)

    assert results == expected_values


# Hook System Tests


def test_hook_initialization(agent):
    """Test that hook system is properly initialized."""
    # Verify hook attributes exist and are properly initialized
    assert hasattr(agent, "_hook_handlers")
    assert hasattr(agent, "_hooks_enabled")
    assert isinstance(agent._hook_handlers, dict)
    assert agent._hooks_enabled is True
    assert len(agent._hook_handlers) == 0


def test_hook_registration(agent):
    """Test hook registration and unregistration functionality."""
    # Test registration
    handler_called = []

    def test_handler(error):
        handler_called.append(error)

    agent.register_hook("parse:error", test_handler)

    # Verify internal storage
    assert "parse:error" in agent._hook_handlers
    assert test_handler in agent._hook_handlers["parse:error"]

    # Test unregistration
    agent.unregister_hook("parse:error", test_handler)
    assert test_handler not in agent._hook_handlers["parse:error"]


def test_hook_registration_with_instructor_client(mock_instructor):
    """Test that hooks are registered with instructor client when available."""
    # Add hook methods to mock instructor
    mock_instructor.on = Mock()
    mock_instructor.off = Mock()
    mock_instructor.clear = Mock()

    config = AgentConfig(client=mock_instructor, model="gpt-5-mini")
    agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)

    def test_handler(error):
        pass

    # Test registration delegates to instructor client
    agent.register_hook("parse:error", test_handler)
    mock_instructor.on.assert_called_once_with("parse:error", test_handler)

    # Test unregistration delegates to instructor client
    agent.unregister_hook("parse:error", test_handler)
    mock_instructor.off.assert_called_once_with("parse:error", test_handler)


def test_multiple_hook_handlers(agent):
    """Test multiple handlers for the same event."""
    handler1_calls = []
    handler2_calls = []

    def handler1(error):
        handler1_calls.append(error)

    def handler2(error):
        handler2_calls.append(error)

    # Register multiple handlers
    agent.register_hook("parse:error", handler1)
    agent.register_hook("parse:error", handler2)

    # Verify both are registered
    assert len(agent._hook_handlers["parse:error"]) == 2
    assert handler1 in agent._hook_handlers["parse:error"]
    assert handler2 in agent._hook_handlers["parse:error"]

    # Test dispatch to both handlers
    test_error = Exception("test error")
    agent._dispatch_hook("parse:error", test_error)

    assert len(handler1_calls) == 1
    assert len(handler2_calls) == 1
    assert handler1_calls[0] is test_error
    assert handler2_calls[0] is test_error


def test_hook_clear_specific_event(agent):
    """Test clearing hooks for a specific event."""

    def handler1():
        pass

    def handler2():
        pass

    # Register handlers for different events
    agent.register_hook("parse:error", handler1)
    agent.register_hook("completion:error", handler2)

    # Clear specific event
    agent.clear_hooks("parse:error")

    # Verify only parse:error was cleared
    assert len(agent._hook_handlers["parse:error"]) == 0
    assert handler2 in agent._hook_handlers["completion:error"]


def test_hook_clear_all_events(agent):
    """Test clearing all hooks."""

    def handler1():
        pass

    def handler2():
        pass

    # Register handlers for different events
    agent.register_hook("parse:error", handler1)
    agent.register_hook("completion:error", handler2)

    # Clear all hooks
    agent.clear_hooks()

    # Verify all hooks are cleared
    assert len(agent._hook_handlers) == 0


def test_hook_enable_disable(agent):
    """Test hook enable/disable functionality."""
    # Test initial state
    assert agent.hooks_enabled is True

    # Test disable
    agent.disable_hooks()
    assert agent.hooks_enabled is False
    assert agent._hooks_enabled is False

    # Test enable
    agent.enable_hooks()
    assert agent.hooks_enabled is True
    assert agent._hooks_enabled is True


def test_hook_dispatch_when_disabled(agent):
    """Test that hooks don't execute when disabled."""
    handler_called = []

    def test_handler(error):
        handler_called.append(error)

    agent.register_hook("parse:error", test_handler)

    # Disable hooks
    agent.disable_hooks()

    # Dispatch should not call handler
    agent._dispatch_hook("parse:error", Exception("test"))
    assert len(handler_called) == 0

    # Re-enable and test
    agent.enable_hooks()
    agent._dispatch_hook("parse:error", Exception("test"))
    assert len(handler_called) == 1


def test_hook_error_isolation(agent):
    """Test that hook handler errors don't interrupt main flow."""
    good_handler_called = []

    def bad_handler(error):
        raise RuntimeError("Handler error")

    def good_handler(error):
        good_handler_called.append(error)

    # Register both handlers
    agent.register_hook("test:event", bad_handler)
    agent.register_hook("test:event", good_handler)

    # Dispatch should not raise exception
    with patch("logging.getLogger") as mock_logger:
        mock_log = Mock()
        mock_logger.return_value = mock_log

        agent._dispatch_hook("test:event", Exception("test"))

        # Verify error was logged
        mock_log.warning.assert_called_once()

        # Verify good handler still executed
        assert len(good_handler_called) == 1


def test_hook_dispatch_nonexistent_event(agent):
    """Test dispatching to nonexistent event."""
    # Should not raise exception
    agent._dispatch_hook("nonexistent:event", Exception("test"))


def test_hook_unregister_nonexistent_handler(agent):
    """Test unregistering handler that doesn't exist."""

    def test_handler():
        pass

    # Should not raise exception
    agent.unregister_hook("parse:error", test_handler)


def test_agent_initialization_includes_hooks(mock_instructor, mock_history, mock_system_prompt_generator):
    """Test that agent initialization properly sets up hook system."""
    config = AgentConfig(
        client=mock_instructor,
        model="gpt-5-mini",
        history=mock_history,
        system_prompt_generator=mock_system_prompt_generator,
    )

    agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)

    # Verify hook system is initialized
    assert hasattr(agent, "_hook_handlers")
    assert hasattr(agent, "_hooks_enabled")
    assert agent._hooks_enabled is True
    assert isinstance(agent._hook_handlers, dict)
    assert len(agent._hook_handlers) == 0

    # Verify hook management methods exist
    assert hasattr(agent, "register_hook")
    assert hasattr(agent, "unregister_hook")
    assert hasattr(agent, "clear_hooks")
    assert hasattr(agent, "enable_hooks")
    assert hasattr(agent, "disable_hooks")
    assert hasattr(agent, "hooks_enabled")
    assert hasattr(agent, "_dispatch_hook")


def test_backward_compatibility_no_breaking_changes(mock_instructor, mock_history, mock_system_prompt_generator):
    """Test that hook system addition doesn't break existing functionality."""
    # Ensure mock_history.get_history() returns an empty list
    mock_history.get_history.return_value = []

    # Ensure the copy method returns a properly configured mock
    copied_mock = Mock(spec=ChatHistory)
    copied_mock.get_history.return_value = []
    mock_history.copy.return_value = copied_mock

    config = AgentConfig(
        client=mock_instructor,
        model="gpt-5-mini",
        history=mock_history,
        system_prompt_generator=mock_system_prompt_generator,
    )

    agent = AtomicAgent[BasicChatInputSchema, BasicChatOutputSchema](config)

    # Test that all existing attributes still exist and work
    assert agent.client == mock_instructor
    assert agent.model == "gpt-5-mini"
    assert agent.history == mock_history
    assert agent.system_prompt_generator == mock_system_prompt_generator

    # Test that existing methods still work
    # Note: reset_history() changes the history object, so we skip it to focus on core functionality

    # Properties should work
    assert agent.input_schema == BasicChatInputSchema
    assert agent.output_schema == BasicChatOutputSchema

    # Run method should work (with hooks enabled by default)
    user_input = BasicChatInputSchema(chat_message="test")
    response = agent.run(user_input)

    # Verify the response is valid
    assert response is not None

    # Verify the call was made correctly
    mock_instructor.chat.completions.create.assert_called()

    # Test context provider methods still work
    from atomic_agents.context import BaseDynamicContextProvider

    class TestProvider(BaseDynamicContextProvider):
        def get_info(self):
            return "test"

    provider = TestProvider(title="Test")
    agent.register_context_provider("test", provider)

    retrieved = agent.get_context_provider("test")
    assert retrieved == provider

    agent.unregister_context_provider("test")

    # Should raise KeyError for non-existent provider
    with pytest.raises(KeyError):
        agent.get_context_provider("test")
