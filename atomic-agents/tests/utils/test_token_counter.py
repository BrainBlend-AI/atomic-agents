import pytest
from unittest.mock import Mock, patch
from atomic_agents.utils.token_counter import TokenCounter, TokenCountResult


class TestTokenCountResult:
    """Tests for TokenCountResult named tuple."""

    def test_creation_with_all_fields(self):
        result = TokenCountResult(
            total=100,
            system_prompt=30,
            history=70,
            model="gpt-4",
            max_tokens=8192,
            utilization=0.0122,
        )
        assert result.total == 100
        assert result.system_prompt == 30
        assert result.history == 70
        assert result.model == "gpt-4"
        assert result.max_tokens == 8192
        assert result.utilization == 0.0122

    def test_optional_fields_default_to_none(self):
        result = TokenCountResult(
            total=100,
            system_prompt=30,
            history=70,
            model="gpt-4",
        )
        assert result.max_tokens is None
        assert result.utilization is None

    def test_named_tuple_unpacking(self):
        result = TokenCountResult(
            total=100,
            system_prompt=30,
            history=70,
            model="gpt-4",
        )
        total, system_prompt, history, model, max_tokens, utilization = result
        assert total == 100
        assert system_prompt == 30
        assert history == 70
        assert model == "gpt-4"
        assert max_tokens is None
        assert utilization is None

    def test_access_by_index(self):
        result = TokenCountResult(
            total=100,
            system_prompt=30,
            history=70,
            model="gpt-4",
        )
        assert result[0] == 100  # total
        assert result[1] == 30  # system_prompt
        assert result[2] == 70  # history
        assert result[3] == "gpt-4"  # model
        assert result[4] is None  # max_tokens
        assert result[5] is None  # utilization


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
        mock_token_counter.assert_called_once_with(
            model="gpt-4", messages=[{"role": "user", "content": "Hello world"}]
        )

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
        assert result.model == "gpt-4"
        assert result.max_tokens == 8192
        assert result.utilization == pytest.approx(100 / 8192)

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


class TestTokenCounterIntegration:
    """Integration tests that verify the module structure."""

    def test_import_from_utils(self):
        """Test that TokenCounter can be imported from utils."""
        from atomic_agents.utils import TokenCounter, TokenCountResult

        assert TokenCounter is not None
        assert TokenCountResult is not None

    def test_token_counter_instantiation(self):
        """Test that TokenCounter can be instantiated without arguments."""
        counter = TokenCounter()
        assert counter is not None


if __name__ == "__main__":
    pytest.main()
