"""
Console presentation utilities using Rich.

This module provides a clean API for all console output operations.
All Rich-specific code is encapsulated here, making it easy to swap
to a different presentation library if needed.

Design Principles:
- Encapsulate all Rich dependencies
- Provide high-level semantic functions (display_results, not print_table)
- No business logic - only presentation concerns
"""

from contextlib import contextmanager
from typing import Any, Dict, Generator, List

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree

from dspy_integration.domain.models import EvalResult


# Global console instance
console = Console()


# =============================================================================
# HIGH-LEVEL DISPLAY FUNCTIONS
# =============================================================================


def display_welcome(
    title: str,
    subtitle: str,
    details: str,
) -> None:
    """Display welcome banner for the application."""
    console.print(
        Panel.fit(
            f"[bold]{title}[/bold]\n\n{subtitle}\n\n[dim]{details}[/dim]",
            border_style="bold white",
        )
    )


def display_stage_header(stage_name: str, style: str) -> None:
    """Display a stage header with rule line."""
    console.print(Rule(f"[bold {style}]{stage_name}[/bold {style}]", style=style))


def display_panel(
    content: str,
    title: str,
    border_style: str = "blue",
) -> None:
    """Display a panel with formatted content."""
    console.print(Panel(content, title=title, border_style=border_style))


def display_code(
    code: str,
    language: str = "python",
    theme: str = "monokai",
    line_numbers: bool = True,
) -> None:
    """Display syntax-highlighted code."""
    console.print(Syntax(code, language, theme=theme, line_numbers=line_numbers))


def display_step_header(step: str) -> None:
    """Display a step header within a stage."""
    console.print(f"\n[bold]{step}[/bold]")


def display_success(message: str) -> None:
    """Display a success message."""
    console.print(f"[green]✓ {message}[/green]")


def display_info(message: str) -> None:
    """Display an info message."""
    console.print(f"[dim]{message}[/dim]")


def display_tree(
    title: str,
    items: List[Dict[str, Any]],
) -> None:
    """
    Display a tree structure.

    Args:
        title: Root node title
        items: List of dicts with 'title' and optional 'children' keys
    """
    tree = Tree(f"[bold]{title}[/bold]")

    for item in items:
        branch = tree.add(f"[cyan]{item.get('title', 'Item')}[/cyan]")
        for child in item.get("children", []):
            branch.add(child)

    console.print(tree)


# =============================================================================
# RESULTS DISPLAY FUNCTIONS
# =============================================================================


def display_results_table(
    eval_result: EvalResult,
    title: str,
    show_confidence: bool = False,
) -> None:
    """
    Display evaluation results in a table format.

    Args:
        eval_result: Evaluation results to display
        title: Table title
        show_confidence: Whether to show confidence column
    """
    table = Table(
        title=f"{title}: {eval_result.accuracy:.1%} Accuracy " f"({eval_result.correct}/{eval_result.total})",
        box=box.ROUNDED,
    )

    table.add_column("Review", style="cyan", max_width=40)
    table.add_column("Expected", style="green")
    table.add_column("Predicted", style="yellow")

    if show_confidence:
        table.add_column("Confidence", justify="right")

    table.add_column("✓/✗", justify="center")

    for pred in eval_result.predictions:
        row = [
            pred["review"],
            pred["expected"],
            pred["predicted"],
        ]

        if show_confidence:
            row.append(f"{pred['confidence']:.2f}")

        row.append("[green]✓[/green]" if pred["correct"] else "[red]✗[/red]")
        table.add_row(*row)

    console.print(table)


def display_comparison_table(
    stage1_result: EvalResult,
    stage2_result: EvalResult,
    stage3_result: EvalResult,
) -> None:
    """Display side-by-side comparison of all three approaches."""
    table = Table(title="Approach Comparison", box=box.DOUBLE_EDGE)

    table.add_column("Metric", style="bold")
    table.add_column("Stage 1\nRaw DSPy", justify="center", style="blue")
    table.add_column("Stage 2\nRaw Atomic Agents", justify="center", style="magenta")
    table.add_column("Stage 3\nDSPy + Atomic", justify="center", style="green")

    # Accuracy row
    table.add_row(
        "Accuracy",
        f"{stage1_result.accuracy:.1%}",
        f"{stage2_result.accuracy:.1%}",
        f"[bold]{stage3_result.accuracy:.1%}[/bold]",
    )

    # Correct/Total row
    table.add_row(
        "Correct / Total",
        f"{stage1_result.correct}/{stage1_result.total}",
        f"{stage2_result.correct}/{stage2_result.total}",
        f"[bold]{stage3_result.correct}/{stage3_result.total}[/bold]",
    )

    # Time row
    table.add_row(
        "Avg Time/Query",
        f"{stage1_result.avg_time:.2f}s",
        f"{stage2_result.avg_time:.2f}s",
        f"{stage3_result.avg_time:.2f}s",
    )

    # Feature comparison rows
    _add_feature_rows(table)

    console.print(table)


def _add_feature_rows(table: Table) -> None:
    """Add feature comparison rows to the table."""
    features = [
        (
            "Prompt Optimization",
            "[green]✓ Auto[/green]",
            "[red]✗ Manual[/red]",
            "[green]✓ Auto[/green]",
        ),
        (
            "Type Safety",
            "[yellow]~ DSPy Literal[/yellow]",
            "[green]✓ Pydantic[/green]",
            "[green]✓ Pydantic[/green]",
        ),
        (
            "Output Validation",
            "[yellow]~ Basic[/yellow]",
            "[green]✓ Full[/green]",
            "[green]✓ Full[/green]",
        ),
        (
            "Pydantic Ecosystem",
            "[red]✗ No[/red]",
            "[green]✓ Full[/green]",
            "[green]✓ Full[/green]",
        ),
        (
            "Few-Shot Selection",
            "[green]✓ Auto[/green]",
            "[red]✗ Manual[/red]",
            "[green]✓ Auto[/green]",
        ),
        (
            "IDE Support",
            "[yellow]~ Partial[/yellow]",
            "[green]✓ Full[/green]",
            "[green]✓ Full[/green]",
        ),
    ]

    for feature in features:
        table.add_row(*feature)


# =============================================================================
# SUMMARY DISPLAY FUNCTIONS
# =============================================================================


def display_takeaways() -> None:
    """Display key takeaways panel."""
    content = """[bold yellow]KEY TAKEAWAYS[/bold yellow]

[blue]RAW DSPy (with typed signatures):[/blue]
• Excellent optimization with Literal type constraints
• Great for experimentation and iteration
• Missing Pydantic ecosystem (validators, Field constraints)

[magenta]RAW ATOMIC AGENTS:[/magenta]
• Full Pydantic ecosystem with runtime validation
• Instructor integration for robust outputs
• Manual prompt engineering limits optimization

[green]DSPy + ATOMIC AGENTS:[/green]
• Automatic optimization finds the best prompts
• Full Pydantic validation and serialization
• Measurable improvements + production-ready types
• [bold]The best of both worlds![/bold]"""

    console.print(Panel(content, title="Summary", border_style="yellow"))


def display_decision_guide() -> None:
    """Display when-to-use-what guide."""
    content = """[bold]WHEN TO USE EACH APPROACH[/bold]

[blue]Use Raw DSPy when:[/blue]
• Quick prototyping and experimentation
• Output format doesn't matter much
• You'll post-process outputs anyway

[magenta]Use Raw Atomic Agents when:[/magenta]
• You need guaranteed output structure NOW
• You don't have training data for optimization
• The task is simple enough that manual prompts work

[green]Use DSPy + Atomic Agents when:[/green]
• You have labeled data and want to optimize
• Production systems need type-safe outputs
• You want measurable, reproducible improvements
• Both accuracy AND structure matter"""

    console.print(Panel(content, title="Decision Guide", border_style="cyan"))


# =============================================================================
# PROGRESS CONTEXT MANAGER
# =============================================================================


@contextmanager
def create_progress_context(
    description: str,
    style: str = "cyan",
) -> Generator[Progress, None, None]:
    """
    Create a progress context for long-running operations.

    Args:
        description: Task description to display
        style: Color style for the progress text

    Yields:
        Progress object that can be used to update progress

    Example:
        >>> with create_progress_context("Processing...", "green") as progress:
        ...     task = progress.add_task("[green]Working...", total=100)
        ...     for i in range(100):
        ...         progress.advance(task)
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        yield progress
