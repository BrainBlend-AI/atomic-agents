"""
DSPy + Atomic Agents Integration

This module provides a seamless integration between DSPy's declarative prompt optimization
framework and Atomic Agents' type-safe structured output system.

Key Components:
- DSPyAtomicModule: A DSPy module that wraps Atomic Agents for structured outputs
- AtomicSignature: Bridge between Pydantic schemas and DSPy signatures
- Optimization utilities for improving agent performance with few-shot learning
"""

from dspy_integration.bridge import (
    DSPyAtomicModule,
    pydantic_to_dspy_fields,
    create_dspy_signature_from_schemas,
)
from dspy_integration.schemas import (
    SentimentInputSchema,
    SentimentOutputSchema,
    QuestionInputSchema,
    AnswerOutputSchema,
    SummaryInputSchema,
    SummaryOutputSchema,
)

__all__ = [
    "DSPyAtomicModule",
    "pydantic_to_dspy_fields",
    "create_dspy_signature_from_schemas",
    "SentimentInputSchema",
    "SentimentOutputSchema",
    "QuestionInputSchema",
    "AnswerOutputSchema",
    "SummaryInputSchema",
    "SummaryOutputSchema",
]
