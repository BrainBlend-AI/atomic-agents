"""
Domain layer for DSPy + Atomic Agents integration.

This package contains:
- models: Pydantic schemas and data transfer objects
- datasets: Training and test data
- evaluation: Metrics and evaluation utilities

Following Clean Architecture principles, this layer has no dependencies
on external frameworks (except Pydantic for data modeling).
"""

from dspy_integration.domain.models import (
    GenreType,
    GENRES,
    MovieGenreOutput,
    MovieReviewInput,
    EvalResult,
)
from dspy_integration.domain.datasets import TRAINING_DATASET, TEST_DATASET
from dspy_integration.domain.evaluation import evaluate_predictions

__all__ = [
    # Types
    "GenreType",
    "GENRES",
    # Schemas
    "MovieGenreOutput",
    "MovieReviewInput",
    # Data structures
    "EvalResult",
    # Datasets
    "TRAINING_DATASET",
    "TEST_DATASET",
    # Evaluation
    "evaluate_predictions",
]
