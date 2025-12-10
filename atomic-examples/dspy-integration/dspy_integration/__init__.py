"""
DSPy + Atomic Agents Integration Package.

This package demonstrates how to combine DSPy's automatic prompt optimization
with Atomic Agents' type-safe structured outputs.

Package Structure:
    domain/      - Core business logic (models, datasets, evaluation)
    stages/      - Demonstration stages (dspy, atomic, combined)
    presentation/ - UI layer (Rich console output)
    bridge.py    - DSPy ↔ Atomic Agents integration module

Quick Start:
    >>> from dspy_integration import DSPyAtomicModule, MovieReviewInput, MovieGenreOutput
    >>> module = DSPyAtomicModule(
    ...     input_schema=MovieReviewInput,
    ...     output_schema=MovieGenreOutput,
    ...     use_chain_of_thought=True,
    ... )
    >>> result = module.run_validated(review="Amazing action movie!")
    >>> print(result.genre)  # Type-safe output!

Run Demo:
    uv run python -m dspy_integration.main
"""

# Domain exports
from dspy_integration.domain.models import (
    GENRES,
    GenreType,
    MovieGenreOutput,
    MovieReviewInput,
    EvalResult,
)
from dspy_integration.domain.datasets import TRAINING_DATASET, TEST_DATASET
from dspy_integration.domain.evaluation import evaluate_predictions

# Bridge exports
from dspy_integration.bridge import (
    DSPyAtomicModule,
    DSPyAtomicPipeline,
    create_dspy_example,
    create_dspy_signature_from_schemas,
    pydantic_to_dspy_fields,
)

# Original schemas (for backwards compatibility)
from dspy_integration.schemas import (
    SentimentInputSchema,
    SentimentOutputSchema,
    QuestionInputSchema,
    AnswerOutputSchema,
    SummaryInputSchema,
    SummaryOutputSchema,
)

# Stage exports (for advanced usage)
from dspy_integration.stages import (
    run_stage1_raw_dspy,
    run_stage2_raw_atomic_agents,
    run_stage3_combined,
)

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Domain - Types
    "GENRES",
    "GenreType",
    # Domain - Schemas (new)
    "MovieGenreOutput",
    "MovieReviewInput",
    # Domain - Data structures
    "EvalResult",
    # Domain - Datasets
    "TRAINING_DATASET",
    "TEST_DATASET",
    # Domain - Evaluation
    "evaluate_predictions",
    # Bridge - Core classes
    "DSPyAtomicModule",
    "DSPyAtomicPipeline",
    # Bridge - Utilities
    "create_dspy_example",
    "create_dspy_signature_from_schemas",
    "pydantic_to_dspy_fields",
    # Original schemas (backwards compatibility)
    "SentimentInputSchema",
    "SentimentOutputSchema",
    "QuestionInputSchema",
    "AnswerOutputSchema",
    "SummaryInputSchema",
    "SummaryOutputSchema",
    # Stages - Runners
    "run_stage1_raw_dspy",
    "run_stage2_raw_atomic_agents",
    "run_stage3_combined",
]
