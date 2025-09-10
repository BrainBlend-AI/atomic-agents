"""Service layer for managing resources."""

from typing import Dict, List
import re
import inspect
from mcp.server.fastmcp import FastMCP
from example_mcp_server.interfaces.resource import Resource, ResourceResponse


class ResourceService:
    """Service for managing and executing resources."""

    def __init__(self):
        self._resources: Dict[str, Resource] = {}
        self._uri_patterns: Dict[str, Resource] = {}

    def register_resource(self, resource: Resource) -> None:
        """Register a new resource."""
        # Store the resource by its URI pattern for handler registration
        self._uri_patterns[resource.uri] = resource

        # If the URI doesn't have parameters, also store by exact URI
        if "{" not in resource.uri:
            self._resources[resource.uri] = resource

    def register_resources(self, resources: List[Resource]) -> None:
        """Register multiple resources."""
        for resource in resources:
            self.register_resource(resource)

    def get_resource_by_pattern(self, uri_pattern: str) -> Resource:
        """Get a resource by its URI pattern."""
        if uri_pattern not in self._uri_patterns:
            raise ValueError(f"Resource not found for pattern: {uri_pattern}")
        return self._uri_patterns[uri_pattern]

    def get_resource(self, uri: str) -> Resource:
        """Get a resource by exact URI."""
        # First check if there's an exact match for the URI
        if uri in self._resources:
            return self._resources[uri]

        # If not, try to find a pattern that matches
        for pattern, resource in self._uri_patterns.items():
            # Convert the pattern to a regex by replacing {param} with (?P<param>[^/]+)
            regex_pattern = re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", pattern)
            # Ensure we match the whole URI by adding anchors
            regex_pattern = f"^{regex_pattern}$"

            match = re.match(regex_pattern, uri)
            if match:
                # Found a matching pattern, extract parameters
                # Cache the resource with the specific URI for future lookups
                self._resources[uri] = resource
                return resource

        raise ValueError(f"Resource not found: {uri}")

    def extract_params_from_uri(self, pattern: str, uri: str) -> Dict[str, str]:
        """Extract parameters from a URI based on a pattern."""
        # Convert the pattern to a regex by replacing {param} with (?P<param>[^/]+)
        regex_pattern = re.sub(r"\{([^}]+)\}", r"(?P<\1>[^/]+)", pattern)
        # Ensure we match the whole URI by adding anchors
        regex_pattern = f"^{regex_pattern}$"

        match = re.match(regex_pattern, uri)
        if match:
            return match.groupdict()
        return {}

    def create_handler(self, resource: Resource, uri_pattern: str):
        """Create a handler function for a resource with the correct parameters."""
        # Extract parameters from URI pattern
        uri_params = set(re.findall(r"\{([^}]+)\}", uri_pattern))

        if not uri_params:
            # For static resources with no parameters
            async def static_handler() -> ResourceResponse:
                """Handle static resource request."""
                # Create empty input for resources without parameters
                input_data = resource.input_model()
                return await resource.read(input_data)

            # Set metadata for the handler
            static_handler.__name__ = resource.name
            static_handler.__doc__ = resource.description
            return static_handler
        else:
            # For resources with parameters
            # Create parameters for the signature
            uri_params_list = list(uri_params)
            sig = inspect.Signature(
                [
                    inspect.Parameter(param, inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=str)
                    for param in uri_params_list
                ]
            )

            # Create the handler function
            async def param_handler(*args, **kwargs):
                """Handle parameterized resource request."""
                # Bind the arguments to the signature
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                # Create input data from bound arguments
                input_data = resource.input_model(**bound_args.arguments)
                return await resource.read(input_data)

            # Set the signature and metadata on the handler
            param_handler.__signature__ = sig
            param_handler.__name__ = resource.name
            param_handler.__doc__ = resource.description

            # Set annotations
            param_handler.__annotations__ = {param: str for param in uri_params_list}
            param_handler.__annotations__["return"] = ResourceResponse

            return param_handler

    def register_mcp_handlers(self, mcp: FastMCP) -> None:
        """Register all resources as MCP handlers."""
        for uri_pattern, resource in self._uri_patterns.items():
            handler = self.create_handler(resource, uri_pattern)

            # Register the resource with the full metadata
            wrapped_handler = mcp.resource(
                uri=uri_pattern, name=resource.name, description=resource.description, mime_type=resource.mime_type
            )(handler)

            # Ensure the handler's metadata is preserved
            wrapped_handler.__name__ = resource.name
            wrapped_handler.__doc__ = resource.description
