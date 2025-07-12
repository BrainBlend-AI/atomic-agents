"""
Atomic Agents - A modular framework for building AI agents.
"""

# Core exports - only the most essential classes
from .agents.base_agent import BaseAgent, BaseAgentConfig
from .lib.base.base_io_schema import BaseIOSchema

# Version info
__version__ = "2.0.0"

# Public API - Core essentials only
__all__ = [
    "BaseAgent",
    "BaseAgentConfig",
    "BaseIOSchema",
]
