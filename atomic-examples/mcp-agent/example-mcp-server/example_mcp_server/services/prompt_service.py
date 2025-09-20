"""Service layer for managing prompts."""

from typing import Dict, List, Any
import logging
import inspect
from mcp.server.fastmcp import FastMCP
from example_mcp_server.interfaces.prompt import Prompt, PromptResponse, PromptContent


class PromptService:
    """Service for managing and executing prompts."""

    def __init__(self):
        self._prompts: Dict[str, Prompt] = {}

    def register_prompt(self, prompt: Prompt) -> None:
        """Register a new prompt."""
        self._prompts[prompt.name] = prompt

    def register_prompts(self, prompts: List[Prompt]) -> None:
        """Register multiple prompts."""
        for prompt in prompts:
            self.register_prompt(prompt)

    def get_prompt(self, prompt_name: str) -> Prompt:
        """Get a prompt by name."""
        if prompt_name not in self._prompts:
            raise ValueError(f"Prompt not found: {prompt_name}")
        return self._prompts[prompt_name]

    async def generate_prompt(self, prompt_name: str, input_data: Dict[str, Any]) -> PromptResponse:
        """Execute a prompt by name with given arguments.

        This validates the input against the prompt's input model and calls
        the prompt's async generate method.
        """
        prompt = self.get_prompt(prompt_name)

        # Validate input using Pydantic model_validate to support nested models
        input_model = prompt.input_model.model_validate(input_data)

        return await prompt.generate(input_model)

    def _process_prompt_content(self, content: PromptContent) -> str | Dict[str, Any] | None:
        """Process a PromptContent object into a serializable form."""
        if content.type == "text":
            return content.text
        elif content.type == "json" and content.json_data is not None:
            return content.json_data
        else:
            return content.text or content.json_data or {}

    def _serialize_response(self, response: PromptResponse) -> Any:
        """Serialize a PromptResponse to return to clients.

        If there's a single content item, return it directly; otherwise return a list.
        """
        if not response.content:
            return {}

        if len(response.content) == 1:  # Not a list
            return self._process_prompt_content(response.content[0])

        return [self._process_prompt_content(content) for content in response.content]

    def register_mcp_handlers(self, mcp: FastMCP) -> None:
        """Register all prompts as MCP handlers."""
        for prompt in self._prompts.values():
            # Create a handler that uses the prompt's Pydantic input model directly for schema generation
            def create_handler(prompt: Prompt):
                # Get the fields of the input_model
                input_fields = prompt.input_model.model_fields

                sig = inspect.Signature(
                    [
                        inspect.Parameter(
                            field_name,
                            inspect.Parameter.POSITIONAL_OR_KEYWORD,
                            annotation=field_info.annotation,
                        )
                        for field_name, field_info in input_fields.items()
                    ]
                )

                # Create the handler function
                async def handler(*args, **kwargs):
                    """Execute the prompt with the given input data."""
                    # Bind the arguments to the signature
                    bound_args = sig.bind(*args, **kwargs)
                    bound_args.apply_defaults()

                    input_data = dict(bound_args.arguments)
                    logger = logging.getLogger("example_mcp_server.prompt_service")
                    logger.debug("Received input_data for prompt '%s': %s", prompt.name, input_data)

                    # Validate the input using the Pydantic model
                    input_model = prompt.input_model.model_validate(input_data)
                    result = await self.generate_prompt(prompt.name, input_model.model_dump())
                    return self._serialize_response(result)

                # Set the signature and metadata on the handler
                handler.__signature__ = sig
                handler.__name__ = prompt.name
                handler.__doc__ = prompt.description or ""

                # Set annotations
                handler.__annotations__ = {
                    field_name: field_info.annotation for field_name, field_info in input_fields.items()
                }
                handler.__annotations__["return"] = Any

                return handler

            handler = create_handler(prompt)

            # Register the prompt with FastMCP. Use the prompt name as the handler name.
            mcp.prompt(name=prompt.name, description=prompt.description)(handler)
