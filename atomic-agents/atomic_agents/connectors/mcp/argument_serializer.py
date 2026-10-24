"""Serialize explicitly supplied MCP arguments without widening server nullability."""

from typing import Any
from urllib.parse import unquote

from jsonschema import Draft202012Validator
from referencing import Registry
from referencing.exceptions import Unresolvable


class ArgumentSerializer:
    """Remove nonnullable object members while preserving explicit nullable values."""

    def __init__(self, schema: dict[str, Any]) -> None:
        self.schema = schema
        # MCP's schema transformer supports local references. Do not fetch remote schemas.
        self.validator = Draft202012Validator(schema, registry=Registry())

    def _is_valid(self, value: Any, schema: Any) -> bool:
        try:
            return self.validator.evolve(schema=schema).is_valid(value)
        except Unresolvable:
            # Match the transformer's Any fallback for unresolved references.
            return True

    def _resolve_ref(self, reference: str) -> Any:
        if reference == "#":
            return self.schema
        if not reference.startswith("#/"):
            return {}
        schema: Any = self.schema
        for token in unquote(reference[2:]).split("/"):
            if not isinstance(schema, dict):
                return {}
            schema = schema.get(token.replace("~1", "/").replace("~0", "~"), {})
        return schema

    def serialize(self, value: Any) -> Any:
        """Filter a model dump that already excludes unset fields and the tool name."""
        return self._serialize(value, self.schema, frozenset())

    def _serialize(self, value: Any, schema: Any, visited: frozenset[tuple[int, int]]) -> Any:
        if not isinstance(value, (dict, list)) or not isinstance(schema, dict):
            return value
        identity = (id(value), id(schema))
        if identity in visited:
            return value
        visited = visited | {identity}

        if "$ref" in schema:
            value = self._serialize(value, self._resolve_ref(schema["$ref"]), visited)
        for branch in schema.get("allOf", []):
            value = self._serialize(value, branch, visited)

        for keyword in ("anyOf", "oneOf"):
            if keyword not in schema:
                continue
            common = {name: item for name, item in schema.items() if name != keyword}
            for branch in schema[keyword]:
                candidate = self._serialize(value, branch, visited)
                candidate = self._serialize(candidate, common, visited)
                if self._is_valid(candidate, schema):
                    return candidate
            # Do not pick an arbitrary branch when unrelated constraints already fail.
            return value

        if isinstance(value, dict):
            properties = schema.get("properties", {})
            additional = schema.get("additionalProperties", {})
            return {
                name: self._serialize(item, properties.get(name, additional), visited)
                for name, item in value.items()
                if item is not None or self._is_valid(None, properties.get(name, additional))
            }
        items = schema.get("items", {})
        # Array positions are significant; only object members may be omitted.
        return [self._serialize(item, items, visited) for item in value]
