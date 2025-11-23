"""Configuration module for FastAPI Atomic Agents example."""

import os


def get_api_key() -> str:
    """Get OpenAI API key from environment variables.

    Returns:
        str: OpenAI API key

    Raises:
        ValueError: If OPENAI_API_KEY environment variable is not set
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        return api_key

    # Fallback: Try to load from local .env or monorepo quickstart .env
    # This is for development convenience in the atomic-monorepo
    from pathlib import Path

    search_paths = [
        Path(".env"),
        Path("..") / "quickstart" / ".env",
    ]

    for env_path in search_paths:
        if env_path.exists():
            try:
                content = env_path.read_text(encoding="utf-8")
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith("OPENAI_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                continue

    raise ValueError("OPENAI_API_KEY environment variable is required. " "Please set it or create a .env file.")


# Constants
DEFAULT_SESSION_ID = "default"
MODEL_NAME = "gpt-5-mini"
NUM_SUGGESTED_QUESTIONS = 3
