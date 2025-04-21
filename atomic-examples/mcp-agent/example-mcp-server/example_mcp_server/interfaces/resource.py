"""Interfaces for resource abstractions."""

from abc import ABC, abstractmethod
from typing import List, Optional, ClassVar
from pydantic import BaseModel, Field


class ResourceContent(BaseModel):
    """Model for content in resource responses."""

    type: str = Field(default="text")
    text: str
    uri: str
    mime_type: Optional[str] = None


class ResourceResponse(BaseModel):
    """Model for resource responses."""

    contents: List[ResourceContent]


class Resource(ABC):
    """Abstract base class for all resources."""

    name: ClassVar[str]
    description: ClassVar[str]
    uri: ClassVar[str]
    mime_type: ClassVar[Optional[str]] = None

    @abstractmethod
    async def read(self) -> ResourceResponse:
        """Read the resource content."""
        pass
