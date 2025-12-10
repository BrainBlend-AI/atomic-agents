"""
Presentation layer for DSPy + Atomic Agents integration.

This package handles all console output and visualization using Rich.
Separating presentation from business logic allows:
- Testing business logic without UI dependencies
- Easy swapping of presentation implementation
- Clean separation of concerns

Following Clean Architecture: presentation depends on domain, not vice versa.
"""

from dspy_integration.presentation.console import (
    console,
    display_welcome,
    display_stage_header,
    display_panel,
    display_code,
    display_tree,
    display_results_table,
    display_comparison_table,
    display_takeaways,
    display_decision_guide,
    create_progress_context,
)

__all__ = [
    "console",
    "display_welcome",
    "display_stage_header",
    "display_panel",
    "display_code",
    "display_tree",
    "display_results_table",
    "display_comparison_table",
    "display_takeaways",
    "display_decision_guide",
    "create_progress_context",
]
