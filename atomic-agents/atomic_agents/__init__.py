"""
Atomic Agents - A modular framework for building AI agents.
"""

# Core exports - base classes only
from .agents.atomic_agent import AtomicAgent, AgentConfig, BasicChatInputSchema, BasicChatOutputSchema
from .base import BaseIOSchema, BaseTool, BaseToolConfig

# Version info
__version__ = "2.0.0"

__all__ = [
    "AtomicAgent",
    "AgentConfig",
    "BasicChatInputSchema",
    "BasicChatOutputSchema",
    "BaseIOSchema",
    "BaseTool",
    "BaseToolConfig",
]
