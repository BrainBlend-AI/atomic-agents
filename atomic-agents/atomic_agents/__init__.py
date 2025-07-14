"""
Atomic Agents - A modular framework for building AI agents.
"""

# Core exports - base classes only
from .agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema, BaseAgentOutputSchema
from .base import BaseIOSchema, BaseTool, BaseToolConfig

# Version info
__version__ = "2.0.0"

__all__ = [
    "BaseAgent",
    "BaseAgentConfig",
    "BaseAgentInputSchema",
    "BaseAgentOutputSchema",
    "BaseIOSchema",
    "BaseTool",
    "BaseToolConfig",
]
