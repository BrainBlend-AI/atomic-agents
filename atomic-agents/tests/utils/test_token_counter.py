import pytest
from unittest.mock import patch
from atomic_agents.utils.token_counter import (
    TokenCounter,
    TokenCountResult,
    TokenCountError,
    get_token_counter,
)


class TestTokenCountResult:
    """Tests for TokenCountResult named tuple."""

    def test_creation_with_all_fields(self):
        result = TokenCountResult(
            total=100,
            system_prompt=30,
            history=50,
            tools=20,
            model="gpt-4",
            max_tokens=8192,
            utilization=0.0122,
        )
        assert result.total == 100
        assert result.system_prompt == 30
        assert result.history == 50
        assert result.tools == 20
        assert result.model == "gpt-4"
        assert result.max_tokens == 8192
        assert result.utilization == 0.0122

    def test_optional_fields_default_to_none(self):
        result = TokenCountResult(
            total=100,
            system_prompt=30,
            history=50,
            tools=20,
            model="gpt-4",
        )
        assert result.max_tokens is None
        assert result.utilization is None

    def test_named_tuple_unpacking(self):
        result = TokenCountResult(
            total=100,
            system_prompt=30,
            history=50,
            tools=20,
            model="gpt-4",
        )
        total, system_prompt, history, tools, model, max_tokens, utilization = result
        assert total == 100
        assert system_prompt == 30
        assert history == 50
        assert tools == 20
        assert model == "gpt-4"
        assert max_tokens is None
        assert utilization is None

    def test_access_by_index(self):
        result = TokenCountResult(
            total=100,
            system_prompt=30,
            history=50,
            tools=20,
            model="gpt-4",
        )
        assert result[0] == 100  # total
        assert result[1] == 30  # system_prompt
        assert result[2] == 50  # history
        assert result[3] == 20  # tools
        assert result[4] == "gpt-4"  # model
        assert result[5] is None  # max_tokens
        assert result[6] is None  # utilization


class TestTokenCounter:
    """Tests for TokenCounter class."""

    @patch("litellm.token_counter")
    def test_count_messages(self, mock_token_counter):
        mock_token_counter.return_value = 42

        counter = TokenCounter()
        messages = [{"role": "user", "content": "Hello"}]
        result = counter.count_messages("gpt-4", messages)

        assert result == 42
        mock_token_counter.assert_called_once_with(model="gpt-4", messages=messages)

    @patch("litellm.token_counter")
    def test_count_messages_multiple(self, mock_token_counter):
        mock_token_counter.return_value = 100

        counter = TokenCounter()
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        result = counter.count_messages("gpt-4", messages)

        assert result == 100
        mock_token_counter.assert_called_once()

    @patch("litellm.token_counter")
    def test_count_text(self, mock_token_counter):
        mock_token_counter.return_value = 5

        counter = TokenCounter()
        result = counter.count_text("gpt-4", "Hello world")

        assert result == 5
        # Should wrap text in a message
        mock_token_counter.assert_called_once_with(model="gpt-4", messages=[{"role": "user", "content": "Hello world"}])

    @patch("litellm.get_max_tokens")
    def test_get_max_tokens(self, mock_get_max_tokens):
        mock_get_max_tokens.return_value = 8192

        counter = TokenCounter()
        result = counter.get_max_tokens("gpt-4")

        assert result == 8192
        mock_get_max_tokens.assert_called_once_with("gpt-4")

    @patch("litellm.get_max_tokens")
    def test_get_max_tokens_unknown_model(self, mock_get_max_tokens):
        mock_get_max_tokens.side_effect = Exception("Unknown model")

        counter = TokenCounter()
        result = counter.get_max_tokens("unknown-model")

        assert result is None

    @patch("litellm.token_counter")
    def test_count_messages_with_tools(self, mock_token_counter):
        mock_token_counter.return_value = 150

        counter = TokenCounter()
        messages = [{"role": "user", "content": "Hello"}]
        tools = [{"type": "function", "function": {"name": "test_fn"}}]
        result = counter.count_messages("gpt-4", messages, tools=tools)

        assert result == 150
        mock_token_counter.assert_called_once_with(model="gpt-4", messages=messages, tools=tools)

    @patch("litellm.token_counter")
    def test_count_messages_raises_token_count_error(self, mock_token_counter):
        mock_token_counter.side_effect = Exception("API error")

        counter = TokenCounter()
        with pytest.raises(TokenCountError) as exc_info:
            counter.count_messages("gpt-4", [{"role": "user", "content": "test"}])

        assert "Failed to count tokens for model 'gpt-4'" in str(exc_info.value)

    def test_count_messages_raises_value_error_for_empty_model(self):
        counter = TokenCounter()
        with pytest.raises(ValueError) as exc_info:
            counter.count_messages("", [{"role": "user", "content": "test"}])

        assert "model is required" in str(exc_info.value)

    @patch("litellm.get_max_tokens")
    @patch("litellm.token_counter")
    def test_count_context(self, mock_token_counter, mock_get_max_tokens):
        mock_token_counter.side_effect = [30, 70]  # system, then history
        mock_get_max_tokens.return_value = 8192

        counter = TokenCounter()
        result = counter.count_context(
            model="gpt-4",
            system_messages=[{"role": "system", "content": "You are helpful"}],
            history_messages=[{"role": "user", "content": "Hello"}],
        )

        assert result.total == 100
        assert result.system_prompt == 30
        assert result.history == 70
        assert result.tools == 0
        assert result.model == "gpt-4"
        assert result.max_tokens == 8192
        assert result.utilization == pytest.approx(100 / 8192)

    @patch("litellm.get_max_tokens")
    @patch("litellm.token_counter")
    def test_count_context_with_tools(self, mock_token_counter, mock_get_max_tokens):
        # system=30, history=70, empty_with_tools=60, empty_without_tools=10 -> tools=50
        mock_token_counter.side_effect = [30, 70, 60, 10]
        mock_get_max_tokens.return_value = 8192

        counter = TokenCounter()
        tools = [{"type": "function", "function": {"name": "test_fn"}}]
        result = counter.count_context(
            model="gpt-4",
            system_messages=[{"role": "system", "content": "You are helpful"}],
            history_messages=[{"role": "user", "content": "Hello"}],
            tools=tools,
        )

        assert result.system_prompt == 30
        assert result.history == 70
        assert result.tools == 50
        assert result.total == 150  # 30 + 70 + 50
        assert result.model == "gpt-4"

    @patch("litellm.get_max_tokens")
    @patch("litellm.token_counter")
    def test_count_context_empty_system(self, mock_token_counter, mock_get_max_tokens):
        mock_token_counter.return_value = 50
        mock_get_max_tokens.return_value = 4096

        counter = TokenCounter()
        result = counter.count_context(
            model="gpt-3.5-turbo",
            system_messages=[],  # No system prompt
            history_messages=[{"role": "user", "content": "Hello"}],
        )

        assert result.total == 50
        assert result.system_prompt == 0
        assert result.history == 50
        assert result.model == "gpt-3.5-turbo"
        assert result.max_tokens == 4096

    @patch("litellm.get_max_tokens")
    @patch("litellm.token_counter")
    def test_count_context_no_max_tokens(self, mock_token_counter, mock_get_max_tokens):
        mock_token_counter.side_effect = [20, 30]
        mock_get_max_tokens.return_value = None  # Unknown model

        counter = TokenCounter()
        result = counter.count_context(
            model="custom-model",
            system_messages=[{"role": "system", "content": "Test"}],
            history_messages=[{"role": "user", "content": "Test"}],
        )

        assert result.total == 50
        assert result.max_tokens is None
        assert result.utilization is None

    @patch("litellm.token_counter")
    def test_count_messages_different_models(self, mock_token_counter):
        mock_token_counter.return_value = 10
        counter = TokenCounter()

        # Test various model formats
        models = [
            "gpt-4",
            "gpt-3.5-turbo",
            "claude-3-opus-20240229",
            "anthropic/claude-3-sonnet",
            "gemini-pro",
            "gemini/gemini-1.5-pro",
        ]

        for model in models:
            result = counter.count_messages(model, [{"role": "user", "content": "test"}])
            assert result == 10

        # Verify all models were called
        assert mock_token_counter.call_count == len(models)

    @patch("litellm.get_max_tokens")
    @patch("litellm.token_counter")
    def test_count_context_division_by_zero_prevention(self, mock_token_counter, mock_get_max_tokens):
        """Test that division by zero is prevented when max_tokens is 0."""
        mock_token_counter.side_effect = [20, 30]
        mock_get_max_tokens.return_value = 0  # Edge case: max_tokens = 0

        counter = TokenCounter()
        result = counter.count_context(
            model="custom-model",
            system_messages=[{"role": "system", "content": "Test"}],
            history_messages=[{"role": "user", "content": "Test"}],
        )

        assert result.total == 50
        assert result.max_tokens == 0
        assert result.utilization is None  # Should be None, not raise ZeroDivisionError

    @patch("litellm.get_max_tokens")
    @patch("litellm.token_counter")
    def test_count_context_empty_history(self, mock_token_counter, mock_get_max_tokens):
        """Test counting context with empty history messages."""
        mock_token_counter.return_value = 30  # Only system
        mock_get_max_tokens.return_value = 4096

        counter = TokenCounter()
        result = counter.count_context(
            model="gpt-4",
            system_messages=[{"role": "system", "content": "You are helpful"}],
            history_messages=[],  # Empty history
        )

        assert result.total == 30
        assert result.system_prompt == 30
        assert result.history == 0
        assert result.tools == 0


class TestGetTokenCounter:
    """Tests for the get_token_counter singleton function."""

    def test_get_token_counter_returns_instance(self):
        """Test that get_token_counter returns a TokenCounter instance."""
        counter = get_token_counter()
        assert isinstance(counter, TokenCounter)

    def test_get_token_counter_returns_same_instance(self):
        """Test that get_token_counter returns the same singleton instance."""
        counter1 = get_token_counter()
        counter2 = get_token_counter()
        assert counter1 is counter2


class TestTokenCountError:
    """Tests for TokenCountError exception."""

    def test_token_count_error_is_exception(self):
        """Test that TokenCountError is an Exception."""
        error = TokenCountError("test error")
        assert isinstance(error, Exception)

    def test_token_count_error_message(self):
        """Test that TokenCountError preserves the error message."""
        error = TokenCountError("Custom error message")
        assert str(error) == "Custom error message"


class TestTokenCounterIntegration:
    """Integration tests that verify the module structure."""

    def test_import_from_utils(self):
        """Test that all exports can be imported from utils."""
        from atomic_agents.utils import (
            TokenCounter,
            TokenCountResult,
            TokenCountError,
            get_token_counter,
        )

        assert TokenCounter is not None
        assert TokenCountResult is not None
        assert TokenCountError is not None
        assert get_token_counter is not None

    def test_token_counter_instantiation(self):
        """Test that TokenCounter can be instantiated without arguments."""
        counter = TokenCounter()
        assert counter is not None


if __name__ == "__main__":
    pytest.main()
