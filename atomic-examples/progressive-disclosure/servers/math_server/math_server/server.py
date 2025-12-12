"""Math MCP Server with arithmetic tools.

This server provides 8 arithmetic operations to demonstrate
progressive disclosure - when combined with other servers,
the agent will select only the relevant math tools.
"""

import math
from fastmcp import FastMCP

mcp = FastMCP("math-server")


@mcp.tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together (a + b). Use for addition operations."""
    return a + b


@mcp.tool
def subtract_numbers(a: float, b: float) -> float:
    """Subtract b from a (a - b). Use for subtraction operations."""
    return a - b


@mcp.tool
def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers (a * b). Use for multiplication operations."""
    return a * b


@mcp.tool
def divide_numbers(a: float, b: float) -> float:
    """Divide a by b (a / b). Use for division operations. Returns error message if b is 0."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b


@mcp.tool
def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent (base ** exponent). Use for exponentiation."""
    return base**exponent


@mcp.tool
def square_root(number: float) -> float:
    """Calculate the square root of a number. Use for sqrt operations."""
    if number < 0:
        raise ValueError("Cannot calculate square root of negative number")
    return math.sqrt(number)


@mcp.tool
def modulo(a: float, b: float) -> float:
    """Calculate the remainder of a divided by b (a % b). Use for modulo operations."""
    return a % b


@mcp.tool
def absolute_value(number: float) -> float:
    """Return the absolute value of a number. Use to remove negative signs."""
    return abs(number)


def main():
    """Run the math server."""
    mcp.run()


if __name__ == "__main__":
    main()
