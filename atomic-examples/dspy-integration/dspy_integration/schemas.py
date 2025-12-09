"""
Pydantic schemas for DSPy + Atomic Agents integration examples.

These schemas demonstrate how to define type-safe input/output contracts
that can be used with both Atomic Agents and DSPy optimization.
"""

from typing import Literal, List, Optional
from pydantic import Field
from atomic_agents.base.base_io_schema import BaseIOSchema


class SentimentInputSchema(BaseIOSchema):
    """Input schema for sentiment analysis task."""

    text: str = Field(
        ...,
        description="The text to analyze for sentiment.",
        min_length=1,
    )


class SentimentOutputSchema(BaseIOSchema):
    """Output schema for sentiment analysis with structured results."""

    sentiment: Literal["positive", "negative", "neutral"] = Field(
        ...,
        description="The overall sentiment of the text.",
    )
    confidence: float = Field(
        ...,
        description="Confidence score between 0 and 1.",
        ge=0.0,
        le=1.0,
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation for the sentiment classification.",
    )


class QuestionInputSchema(BaseIOSchema):
    """Input schema for question answering task."""

    question: str = Field(
        ...,
        description="The question to answer.",
    )
    context: Optional[str] = Field(
        default=None,
        description="Optional context to help answer the question.",
    )


class AnswerOutputSchema(BaseIOSchema):
    """Output schema for question answering with structured response."""

    answer: str = Field(
        ...,
        description="The answer to the question.",
    )
    confidence: float = Field(
        ...,
        description="Confidence score for the answer between 0 and 1.",
        ge=0.0,
        le=1.0,
    )
    sources: List[str] = Field(
        default_factory=list,
        description="List of sources or references used to derive the answer.",
    )


class SummaryInputSchema(BaseIOSchema):
    """Input schema for text summarization task."""

    text: str = Field(
        ...,
        description="The text to summarize.",
    )
    max_sentences: int = Field(
        default=3,
        description="Maximum number of sentences in the summary.",
        ge=1,
        le=10,
    )


class SummaryOutputSchema(BaseIOSchema):
    """Output schema for text summarization with structured results."""

    summary: str = Field(
        ...,
        description="The summarized text.",
    )
    key_points: List[str] = Field(
        ...,
        description="List of key points extracted from the text.",
    )
    word_count: int = Field(
        ...,
        description="Word count of the summary.",
        ge=0,
    )


class ClassificationInputSchema(BaseIOSchema):
    """Input schema for multi-label text classification."""

    text: str = Field(
        ...,
        description="The text to classify.",
    )
    categories: List[str] = Field(
        ...,
        description="Available categories to classify into.",
    )


class ClassificationOutputSchema(BaseIOSchema):
    """Output schema for multi-label classification with confidence scores."""

    labels: List[str] = Field(
        ...,
        description="Assigned labels/categories.",
    )
    label_scores: List[float] = Field(
        ...,
        description="Confidence scores for each assigned label.",
    )
    primary_label: str = Field(
        ...,
        description="The most confident label assignment.",
    )
    reasoning: str = Field(
        ...,
        description="Explanation for the classification decision.",
    )
