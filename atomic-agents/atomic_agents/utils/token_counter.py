"""Token counting utilities for provider-agnostic context measurement."""

import logging
from typing import Any, Dict, List, NamedTuple, Optional

logger = logging.getLogger(__name__)


class TokenCountResult(NamedTuple):
    """
    Result of a token count operation.

    Attributes:
        total: Total number of tokens in the context.
        system_prompt: Tokens in the system prompt (0 if no system prompt).
        history: Tokens in the conversation history.
        model: The model used for tokenization.
        max_tokens: Maximum context window for the model (None if unknown).
        utilization: Percentage of context window used (None if max_tokens unknown).
    """

    total: int
    system_prompt: int
    history: int
    model: str
    max_tokens: Optional[int] = None
    utilization: Optional[float] = None


class TokenCounter:
    """
    Utility class for counting tokens using LiteLLM's provider-agnostic tokenizer.

    This class provides methods for counting tokens in messages, text, and
    retrieving model context limits. It uses LiteLLM's token_counter which
    automatically selects the appropriate tokenizer based on the model.

    Works with any model supported by LiteLLM including:
    - OpenAI (gpt-4, gpt-3.5-turbo, etc.)
    - Anthropic (claude-3-opus, claude-3-sonnet, etc.)
    - Google (gemini-pro, gemini-1.5-pro, etc.)
    - And 100+ other providers

    Example:
        ```python
        counter = TokenCounter()

        # Count tokens in messages
        messages = [{"role": "user", "content": "Hello, world!"}]
        count = counter.count_messages("gpt-4", messages)

        # Get max tokens for a model
        max_tokens = counter.get_max_tokens("gpt-4")
        ```
    """

    def count_messages(self, model: str, messages: List[Dict[str, Any]]) -> int:
        """
        Count the number of tokens in a list of messages.

        Args:
            model: The model identifier (e.g., "gpt-4", "anthropic/claude-3-opus").
            messages: List of message dictionaries with 'role' and 'content' keys.

        Returns:
            The number of tokens in the messages.
        """
        from litellm import token_counter

        return token_counter(model=model, messages=messages)

    def count_text(self, model: str, text: str) -> int:
        """
        Count the number of tokens in a text string.

        Args:
            model: The model identifier.
            text: The text to tokenize.

        Returns:
            The number of tokens in the text.
        """
        from litellm import token_counter

        messages = [{"role": "user", "content": text}]
        return token_counter(model=model, messages=messages)

    def get_max_tokens(self, model: str) -> Optional[int]:
        """
        Get the maximum context window size for a model.

        Args:
            model: The model identifier.

        Returns:
            The maximum number of tokens, or None if unknown.
        """
        try:
            from litellm import get_max_tokens

            return get_max_tokens(model)
        except Exception as e:
            logger.warning(f"Could not determine max tokens for model '{model}': {e}")
            return None

    def count_context(
        self,
        model: str,
        system_messages: List[Dict[str, Any]],
        history_messages: List[Dict[str, Any]],
    ) -> TokenCountResult:
        """
        Count tokens with breakdown by system prompt and history.

        Args:
            model: The model identifier.
            system_messages: System prompt messages (may be empty).
            history_messages: Conversation history messages.

        Returns:
            TokenCountResult with breakdown and utilization metrics.
        """
        system_tokens = self.count_messages(model, system_messages) if system_messages else 0
        history_tokens = self.count_messages(model, history_messages) if history_messages else 0
        total_tokens = system_tokens + history_tokens

        max_tokens = self.get_max_tokens(model)
        utilization = (total_tokens / max_tokens) if max_tokens else None

        return TokenCountResult(
            total=total_tokens,
            system_prompt=system_tokens,
            history=history_tokens,
            model=model,
            max_tokens=max_tokens,
            utilization=utilization,
        )
