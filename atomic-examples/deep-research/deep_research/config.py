import os
from dataclasses import dataclass
from typing import Set


def get_api_key() -> str:
    """Retrieve API key from environment or raise error"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")
    return api_key


def get_searxng_base_url() -> str:
    """Retrieve SearXNG base URL from environment or use default"""
    base_url = os.getenv("SEARXNG_BASE_URL", "http://localhost:8080")
    return base_url


def get_searxng_api_key() -> str:
    """Retrieve SearXNG API key from environment"""
    api_key = os.getenv("SEARXNG_API_KEY")
    return api_key


@dataclass
class ChatConfig:
    """Configuration for the chat application"""

    api_key: str = get_api_key()  # This becomes a class variable
    model: str = "gpt-5-mini"
    reasoning_effort: str = "low"
    exit_commands: Set[str] = frozenset({"/exit", "/quit"})
    searxng_base_url: str = get_searxng_base_url()
    searxng_api_key: str = get_searxng_api_key()

    def __init__(self):
        # Prevent instantiation
        raise TypeError("ChatConfig is not meant to be instantiated")
