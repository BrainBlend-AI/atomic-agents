"""
Atomic Agents - A modular framework for building AI agents.
"""

# Core exports - base classes only
from .agents.atomic_agent import AtomicAgent, AgentConfig, BasicChatInputSchema, BasicChatOutputSchema
from .base import BaseIOSchema, BaseTool, BaseToolConfig

# Version info - read from pyproject.toml via package metadata
from importlib.metadata import version as _version

__version__ = _version("atomic-agents")

__all__ = [
    "AtomicAgent",
    "AgentConfig",
    "BasicChatInputSchema",
    "BasicChatOutputSchema",
    "BaseIOSchema",
    "BaseTool",
    "BaseToolConfig",
]
