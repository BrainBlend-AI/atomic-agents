"""Data MCP Server with list/data manipulation tools.

This server provides 8 data/list operations to demonstrate
progressive disclosure - when combined with other servers,
the agent will select only the relevant data tools.
"""

from typing import List
from fastmcp import FastMCP

mcp = FastMCP("data-server")


@mcp.tool
def sort_list(items: List[float], descending: bool = False) -> List[float]:
    """Sort a list of numbers. Use ascending=True for descending order."""
    return sorted(items, reverse=descending)


@mcp.tool
def filter_greater_than(items: List[float], threshold: float) -> List[float]:
    """Filter list to only include items greater than the threshold."""
    return [x for x in items if x > threshold]


@mcp.tool
def filter_less_than(items: List[float], threshold: float) -> List[float]:
    """Filter list to only include items less than the threshold."""
    return [x for x in items if x < threshold]


@mcp.tool
def sum_list(items: List[float]) -> float:
    """Calculate the sum of all numbers in a list. Use for totaling values."""
    return sum(items)


@mcp.tool
def average_list(items: List[float]) -> float:
    """Calculate the average (mean) of all numbers in a list."""
    if not items:
        return 0.0
    return sum(items) / len(items)


@mcp.tool
def min_value(items: List[float]) -> float:
    """Find the minimum value in a list. Use to find smallest number."""
    if not items:
        raise ValueError("Cannot find minimum of empty list")
    return min(items)


@mcp.tool
def max_value(items: List[float]) -> float:
    """Find the maximum value in a list. Use to find largest number."""
    if not items:
        raise ValueError("Cannot find maximum of empty list")
    return max(items)


@mcp.tool
def unique_values(items: List[float]) -> List[float]:
    """Remove duplicate values from a list, preserving order."""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def main():
    """Run the data server."""
    mcp.run()


if __name__ == "__main__":
    main()
