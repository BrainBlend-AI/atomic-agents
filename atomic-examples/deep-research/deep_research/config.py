import os
from dataclasses import dataclass
from typing import Set


def get_api_key() -> str:
    """Retrieve API key from environment or raise error"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Please set the OPENAI_API_KEY environment variable.")
    return api_key


@dataclass
class ChatConfig:
    """Configuration for the chat application"""

    api_key: str = get_api_key()  # This becomes a class variable
    model: str = "gpt-4o-mini"
    exit_commands: Set[str] = frozenset({"/exit", "/quit"})

    def __init__(self):
        # Prevent instantiation
        raise TypeError("ChatConfig is not meant to be instantiated")
