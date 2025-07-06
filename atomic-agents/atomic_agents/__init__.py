"""
Atomic Agents - A modular framework for building AI agents.
"""

# Core exports for simplified imports
from .agents.base_agent import (
    BaseAgent,
    BaseAgentConfig,
    BaseAgentInputSchema,
    BaseAgentOutputSchema,
)

from .lib.base.base_io_schema import BaseIOSchema
from .lib.base.base_tool import BaseTool, BaseToolConfig

from .lib.components.chat_history import ChatHistory
from .lib.components.system_prompt_generator import (
    SystemPromptGenerator,
    SystemPromptContextProviderBase,
)

# Version info
__version__ = "2.0.0"

# Public API
__all__ = [
    # Agents
    "BaseAgent",
    "BaseAgentConfig", 
    "BaseAgentInputSchema",
    "BaseAgentOutputSchema",
    # Schemas
    "BaseIOSchema",
    # Tools
    "BaseTool",
    "BaseToolConfig",
    # Components
    "ChatHistory",
    "SystemPromptGenerator", 
    "SystemPromptContextProviderBase",
]
