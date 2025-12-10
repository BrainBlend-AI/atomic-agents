"""
Evaluation utilities for comparing classification approaches.

This module provides pure functions for evaluating model predictions.
No side effects, no I/O - just computation.

Design Principles:
- Pure functions with no side effects
- Clear input/output contracts
- Single responsibility (evaluation only)
"""

from typing import Any, Dict, List

from dspy_integration.domain.models import EvalResult


def evaluate_predictions(
    predictions: List[Dict[str, Any]],
    test_set: List[Dict[str, str]],
) -> EvalResult:
    """
    Calculate accuracy and gather evaluation statistics.

    Args:
        predictions: List of prediction dictionaries with 'genre', 'confidence', 'reasoning'
        test_set: List of ground truth examples with 'review' and 'genre'

    Returns:
        EvalResult containing accuracy metrics and detailed prediction results

    Example:
        >>> predictions = [{"genre": "action", "confidence": 0.9, "reasoning": "..."}]
        >>> test_set = [{"review": "...", "genre": "action"}]
        >>> result = evaluate_predictions(predictions, test_set)
        >>> print(f"Accuracy: {result.accuracy:.1%}")
    """
    correct = 0
    results = []

    for pred, truth in zip(predictions, test_set):
        predicted_genre = pred.get("genre", "").lower()
        expected_genre = truth["genre"].lower()
        is_correct = predicted_genre == expected_genre

        if is_correct:
            correct += 1

        results.append(
            {
                "review": _truncate(truth["review"], max_length=50),
                "expected": truth["genre"],
                "predicted": pred.get("genre", "ERROR"),
                "correct": is_correct,
                "confidence": pred.get("confidence", 0),
                "reasoning": _truncate(pred.get("reasoning", "N/A"), max_length=60),
            }
        )

    total = len(test_set)
    accuracy = correct / total if total > 0 else 0.0

    return EvalResult(
        correct=correct,
        total=total,
        accuracy=accuracy,
        predictions=results,
        avg_time=0.0,  # To be set by caller
    )


def _truncate(text: str, max_length: int) -> str:
    """Truncate text with ellipsis if longer than max_length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."
