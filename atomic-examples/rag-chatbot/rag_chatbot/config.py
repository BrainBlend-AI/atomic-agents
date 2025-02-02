import os
from dataclasses import dataclass


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
    exit_commands: set[str] = frozenset({"/exit", "exit", "quit", "/quit"})

    def __init__(self):
        # Prevent instantiation
        raise TypeError("ChatConfig is not meant to be instantiated")


# Model Configuration
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI's latest embedding model
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Vector Search Configuration
NUM_CHUNKS_TO_RETRIEVE = 3
SIMILARITY_METRIC = "cosine"

# ChromaDB Configuration
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")

# Memory Configuration
MEMORY_SIZE = 10  # Number of messages to keep in conversation memory
MAX_CONTEXT_LENGTH = 4000  # Maximum length of combined context to send to the model
