"""Interface definitions for the application."""

from .tool import Tool, BaseToolInput, ToolResponse, ToolContent
from .resource import Resource, BaseResourceInput, ResourceContent, ResourceResponse
from .prompt import Prompt, BasePromptInput, PromptContent, PromptResponse

__all__ = [
    "Tool",
    "BaseToolInput",
    "ToolResponse",
    "ToolContent",
    "Resource",
    "BaseResourceInput",
    "ResourceContent",
    "ResourceResponse",
    "Prompt",
    "BasePromptInput",
    "PromptContent",
    "PromptResponse",
]
