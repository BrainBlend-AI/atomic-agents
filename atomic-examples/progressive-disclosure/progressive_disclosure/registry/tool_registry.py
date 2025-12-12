"""Lightweight tool registry for progressive disclosure.

This module provides a registry that holds tool metadata (name, description, keywords)
without loading the full schema definitions. This enables efficient tool discovery
where the sub-agent can search through available tools without incurring the context
window cost of full schema definitions.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, NamedTuple


class MCPToolDefinition(NamedTuple):
    """Definition of an MCP tool (matching atomic-agents structure)."""

    name: str
    description: Optional[str]
    input_schema: Dict[str, Any]


@dataclass
class ToolMetadata:
    """Lightweight tool representation for search.

    This stores only the essential metadata needed for tool discovery,
    avoiding the full JSON schema that would bloat the context window.
    """

    name: str
    description: str
    keywords: List[str] = field(default_factory=list)
    category: Optional[str] = None

    def to_search_string(self) -> str:
        """Create a searchable string representation."""
        parts = [self.name, self.description]
        if self.keywords:
            parts.extend(self.keywords)
        if self.category:
            parts.append(self.category)
        return " ".join(parts).lower()


class ToolRegistry:
    """Registry that holds tool metadata for progressive discovery.

    The registry stores lightweight metadata about available tools,
    enabling efficient search without loading full schema definitions.
    This is a key component of the progressive disclosure pattern.

    Example:
        >>> registry = ToolRegistry()
        >>> registry.register_from_mcp(mcp_definitions)
        >>> results = registry.search("calculate numbers", max_results=3)
        >>> for tool in results:
        ...     print(f"{tool.name}: {tool.description}")
    """

    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}

    def register(self, metadata: ToolMetadata) -> None:
        """Register a single tool's metadata."""
        self._tools[metadata.name] = metadata

    def register_from_mcp(self, mcp_definitions: List[MCPToolDefinition]) -> None:
        """Register tools from MCP definitions (metadata only, no schemas).

        Args:
            mcp_definitions: List of MCP tool definitions to register.
                            Only name and description are stored.
        """
        for defn in mcp_definitions:
            keywords = self._extract_keywords(defn.description)
            category = self._infer_category(defn.name, defn.description)

            self._tools[defn.name] = ToolMetadata(
                name=defn.name,
                description=defn.description or "",
                keywords=keywords,
                category=category,
            )

    def _extract_keywords(self, description: Optional[str]) -> List[str]:
        """Extract keywords from a tool description.

        Uses simple heuristics to identify important terms:
        - Words longer than 3 characters
        - Words not in common stop words
        - Capitalized words (likely proper nouns or technical terms)
        """
        if not description:
            return []

        # Common stop words to filter out
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "as",
            "is",
            "was",
            "are",
            "were",
            "been",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "shall",
            "can",
            "this",
            "that",
            "these",
            "those",
            "it",
            "its",
            "they",
            "them",
            "their",
            "we",
            "us",
            "our",
            "you",
            "your",
            "i",
            "me",
            "my",
            "he",
            "she",
            "his",
            "her",
            "which",
            "who",
            "whom",
            "what",
            "when",
            "where",
            "why",
            "how",
            "all",
            "each",
            "every",
            "both",
            "few",
            "more",
            "most",
            "other",
            "some",
            "such",
            "no",
            "not",
            "only",
            "own",
            "same",
            "so",
            "than",
            "too",
            "very",
            "just",
            "also",
            "now",
        }

        # Extract words
        words = re.findall(r"\b[a-zA-Z]+\b", description.lower())

        # Filter and deduplicate
        keywords = []
        seen = set()
        for word in words:
            if len(word) > 3 and word not in stop_words and word not in seen:
                keywords.append(word)
                seen.add(word)

        return keywords[:10]  # Limit to top 10 keywords

    def _infer_category(self, name: str, description: Optional[str]) -> Optional[str]:
        """Infer a category for the tool based on name and description.

        Categories help with broad filtering before detailed search.
        """
        text = f"{name} {description or ''}".lower()

        categories = {
            "math": ["add", "subtract", "multiply", "divide", "calculate", "math", "number", "arithmetic"],
            "search": ["search", "find", "query", "lookup", "fetch"],
            "file": ["file", "read", "write", "save", "load", "open", "close"],
            "data": ["data", "database", "sql", "json", "xml", "csv"],
            "web": ["http", "api", "request", "url", "web", "download", "upload"],
            "text": ["text", "string", "parse", "format", "convert"],
        }

        for category, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return category

        return None

    def search(self, query: str, max_results: int = 5, category: Optional[str] = None) -> List[ToolMetadata]:
        """Search for tools matching the query.

        Uses a simple relevance scoring based on:
        - Exact name match (highest weight)
        - Name contains query terms
        - Description contains query terms
        - Keyword matches

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            category: Optional category filter

        Returns:
            List of ToolMetadata sorted by relevance
        """
        query_terms = set(query.lower().split())
        scored_results: List[tuple[float, ToolMetadata]] = []

        for metadata in self._tools.values():
            # Apply category filter if specified
            if category and metadata.category != category:
                continue

            score = self._calculate_relevance(metadata, query_terms)
            if score > 0:
                scored_results.append((score, metadata))

        # Sort by score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)

        return [metadata for _, metadata in scored_results[:max_results]]

    def _calculate_relevance(self, metadata: ToolMetadata, query_terms: set[str]) -> float:
        """Calculate relevance score for a tool against query terms."""
        score = 0.0
        name_lower = metadata.name.lower()
        search_string = metadata.to_search_string()

        for term in query_terms:
            # Exact name match - highest weight
            if term == name_lower:
                score += 10.0

            # Name contains term
            elif term in name_lower:
                score += 5.0

            # Term in description/keywords
            if term in search_string:
                score += 2.0

            # Partial match in keywords
            for keyword in metadata.keywords:
                if term in keyword or keyword in term:
                    score += 1.0

        return score

    def get_all_metadata(self) -> List[ToolMetadata]:
        """Get all tool metadata (for context provider listing)."""
        return list(self._tools.values())

    def get_all_tools(self) -> List[ToolMetadata]:
        """Get all tool metadata (alias for get_all_metadata)."""
        return self.get_all_metadata()

    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        """Get metadata for a specific tool by name."""
        return self._tools.get(name)

    def get_tool_names(self) -> List[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())

    def __len__(self) -> int:
        """Return the number of registered tools."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools

    def get_summary(self) -> str:
        """Get a summary string of all tools for context injection.

        This provides a lightweight overview suitable for the tool finder agent's
        context, listing all available tools without full schema definitions.
        """
        lines = ["Available tools:"]
        for metadata in self._tools.values():
            category_str = f" [{metadata.category}]" if metadata.category else ""
            lines.append(f"- {metadata.name}{category_str}: {metadata.description}")
        return "\n".join(lines)
