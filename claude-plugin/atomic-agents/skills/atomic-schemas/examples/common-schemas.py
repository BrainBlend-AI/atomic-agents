"""Common schema patterns for Atomic Agents applications."""

from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field, field_validator, model_validator
from typing import List, Optional, Literal, Union
from enum import Enum


# ============================================================
# Basic Chat Schemas
# ============================================================

class ChatInputSchema(BaseIOSchema):
    """Standard chat input."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The user's message or question"
    )


class ChatOutputSchema(BaseIOSchema):
    """Standard chat output."""

    response: str = Field(
        ...,
        description="The agent's response to the user"
    )


# ============================================================
# Structured Analysis Output
# ============================================================

class AnalysisOutputSchema(BaseIOSchema):
    """Structured analysis with findings and recommendations."""

    summary: str = Field(
        ...,
        description="Brief summary of the analysis (1-2 sentences)"
    )
    findings: List[str] = Field(
        default_factory=list,
        description="Key findings from the analysis"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0 and 1"
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable recommendations"
    )


# ============================================================
# Classification Schema
# ============================================================

class Intent(str, Enum):
    QUESTION = "question"
    COMMAND = "command"
    FEEDBACK = "feedback"
    GREETING = "greeting"
    OTHER = "other"


class ClassificationOutputSchema(BaseIOSchema):
    """Intent classification result."""

    intent: Intent = Field(
        ...,
        description="The classified intent of the input"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Classification confidence"
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation of the classification"
    )


# ============================================================
# Search Schemas
# ============================================================

class SearchInputSchema(BaseIOSchema):
    """Search query input."""

    query: str = Field(
        ...,
        min_length=1,
        description="Search query text"
    )
    max_results: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    )
    filters: Optional[dict] = Field(
        default=None,
        description="Optional filters to apply"
    )


class SearchResultSchema(BaseIOSchema):
    """Single search result."""

    title: str = Field(..., description="Result title")
    snippet: str = Field(..., description="Text snippet")
    url: Optional[str] = Field(default=None, description="Source URL")
    score: float = Field(..., ge=0, le=1, description="Relevance score")


class SearchOutputSchema(BaseIOSchema):
    """Search results collection."""

    results: List[SearchResultSchema] = Field(
        default_factory=list,
        description="List of search results"
    )
    total_found: int = Field(
        ...,
        ge=0,
        description="Total number of matching results"
    )
    query_time_ms: Optional[int] = Field(
        default=None,
        description="Query execution time in milliseconds"
    )


# ============================================================
# Error Schemas
# ============================================================

class ErrorSchema(BaseIOSchema):
    """Standard error response."""

    error: str = Field(..., description="Error message")
    code: Optional[str] = Field(default=None, description="Error code")
    details: Optional[dict] = Field(default=None, description="Additional details")


# ============================================================
# Validation Example
# ============================================================

class EmailInputSchema(BaseIOSchema):
    """Input with email validation."""

    email: str = Field(..., description="Email address")
    name: str = Field(..., min_length=1, description="Person's name")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.lower().strip()


class DateRangeSchema(BaseIOSchema):
    """Date range with cross-field validation."""

    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        from datetime import datetime
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @model_validator(mode="after")
    def validate_range(self) -> "DateRangeSchema":
        from datetime import datetime
        start = datetime.strptime(self.start_date, "%Y-%m-%d")
        end = datetime.strptime(self.end_date, "%Y-%m-%d")
        if end < start:
            raise ValueError("end_date must be after start_date")
        return self


# ============================================================
# Polymorphic Content
# ============================================================

class TextContentSchema(BaseIOSchema):
    """Text content block."""

    content_type: Literal["text"] = "text"
    text: str = Field(..., description="Text content")


class ImageContentSchema(BaseIOSchema):
    """Image content block."""

    content_type: Literal["image"] = "image"
    url: str = Field(..., description="Image URL")
    alt_text: Optional[str] = Field(default=None, description="Alt text")


class CodeContentSchema(BaseIOSchema):
    """Code content block."""

    content_type: Literal["code"] = "code"
    code: str = Field(..., description="Code content")
    language: str = Field(default="python", description="Programming language")


ContentType = Union[TextContentSchema, ImageContentSchema, CodeContentSchema]


class MessageSchema(BaseIOSchema):
    """Message with polymorphic content."""

    role: Literal["user", "assistant"] = Field(..., description="Message role")
    content: List[ContentType] = Field(..., description="Message content blocks")
