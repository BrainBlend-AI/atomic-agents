"""
Domain models for movie genre classification.

This module defines the core data structures used throughout the application.
All models are framework-agnostic and can be used with both DSPy and Atomic Agents.

Design Principles:
- Single Responsibility: Each class has one reason to change
- Open/Closed: Extend via inheritance, don't modify
- Dependency Inversion: Depend on abstractions (Pydantic BaseModel)
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Literal

from pydantic import Field

from atomic_agents.base.base_io_schema import BaseIOSchema


# =============================================================================
# TYPE DEFINITIONS
# =============================================================================

GENRES: List[str] = ["action", "comedy", "drama", "horror", "sci-fi", "romance"]
"""Valid genre categories for movie classification."""

GenreType = Literal["action", "comedy", "drama", "horror", "sci-fi", "romance"]
"""Type alias constraining genre values to valid options."""


# =============================================================================
# INPUT/OUTPUT SCHEMAS
# =============================================================================


class MovieReviewInput(BaseIOSchema):
    """
    Input schema for movie review classification.

    This schema validates and documents the expected input format.
    Using Pydantic ensures type safety at runtime.
    """

    review: str = Field(
        ...,
        description="The movie review text to classify.",
    )


class MovieGenreOutput(BaseIOSchema):
    """
    Output schema for movie genre classification with structured results.

    This schema guarantees:
    - genre is one of 6 valid options (via Literal type)
    - confidence is between 0.0 and 1.0 (via ge/le constraints)
    - reasoning is always provided
    """

    genre: GenreType = Field(
        ...,
        description="The primary genre of the movie based on the review.",
    )
    confidence: float = Field(
        ...,
        description="Confidence score between 0.0 and 1.0",
        ge=0.0,
        le=1.0,
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation for why this genre was chosen.",
    )


# =============================================================================
# EVALUATION DATA STRUCTURES
# =============================================================================


@dataclass
class EvalResult:
    """
    Stores evaluation results for comparison across approaches.

    This is a simple data class - no behavior, just data.
    Following the principle of separating data from behavior.
    """

    correct: int
    total: int
    accuracy: float
    predictions: List[Dict[str, Any]]
    avg_time: float
