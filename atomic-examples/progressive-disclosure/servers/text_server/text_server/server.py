"""Text MCP Server with text manipulation tools.

This server provides 8 text operations to demonstrate
progressive disclosure - when combined with other servers,
the agent will select only the relevant text tools.
"""

from typing import List
from fastmcp import FastMCP

mcp = FastMCP("text-server")


@mcp.tool
def uppercase(text: str) -> str:
    """Convert text to all uppercase letters. Use for capitalizing text."""
    return text.upper()


@mcp.tool
def lowercase(text: str) -> str:
    """Convert text to all lowercase letters. Use for lowercasing text."""
    return text.lower()


@mcp.tool
def reverse_text(text: str) -> str:
    """Reverse the order of characters in text. Use to flip text backwards."""
    return text[::-1]


@mcp.tool
def word_count(text: str) -> int:
    """Count the number of words in text. Use to count words."""
    return len(text.split())


@mcp.tool
def char_count(text: str, include_spaces: bool = True) -> int:
    """Count the number of characters in text. Can optionally exclude spaces."""
    if not include_spaces:
        text = text.replace(" ", "")
    return len(text)


@mcp.tool
def concatenate(text1: str, text2: str, separator: str = "") -> str:
    """Join two texts together with an optional separator. Use for combining strings."""
    return text1 + separator + text2


@mcp.tool
def replace_text(text: str, search: str, replacement: str) -> str:
    """Replace all occurrences of search string with replacement. Use for find-and-replace."""
    return text.replace(search, replacement)


@mcp.tool
def split_text(text: str, delimiter: str = " ") -> List[str]:
    """Split text into parts using a delimiter. Use to break text into pieces."""
    return text.split(delimiter)


def main():
    """Run the text server."""
    mcp.run()


if __name__ == "__main__":
    main()
