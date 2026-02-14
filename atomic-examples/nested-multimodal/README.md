# Nested Multimodal Example

This example demonstrates how to use the Atomic Agents framework with **nested multimodal content** — images and PDFs inside nested Pydantic schemas, not just at the top level.

This showcases the fixes for:
- [#208](https://github.com/BrainBlend-AI/atomic-agents/issues/208): ChatHistory crashes with `TypeError` when schemas have both multimodal fields and nested Pydantic models
- [#141](https://github.com/BrainBlend-AI/atomic-agents/issues/141): AgentMemory doesn't support multimodal data inside nested schemas

## Features

1. **Nested Multimodal Schemas**: Images embedded inside nested Pydantic models (e.g., `Document.image`)
2. **Mixed Content**: Top-level multimodal fields combined with nested Pydantic context objects
3. **End-to-End Verification**: Verifies the chat history format is correct before making the LLM call

## Getting Started

1. Navigate to the nested-multimodal directory:

   ```bash
   cd atomic-agents/atomic-examples/nested-multimodal
   ```

2. Install dependencies using uv:

   ```bash
   uv sync
   ```

3. Set up environment variables:

   Create a `.env` file with:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   ```

4. Run the example:

   ```bash
   uv run python nested_multimodal/main.py
   ```

## Schema Design

The example uses nested schemas that would have previously caused errors:

```python
class AnalysisContext(BaseIOSchema):
    """Nested context — a plain Pydantic model alongside multimodal fields."""
    focus_area: str
    detail_level: str

class ImageWithContext(BaseIOSchema):
    """Image wrapped in a nested schema with metadata."""
    image: instructor.Image
    label: str

class AnalysisInput(BaseIOSchema):
    """Top-level input combining nested multimodal + nested context."""
    documents: List[ImageWithContext]   # Images nested inside schemas
    context: AnalysisContext            # Nested Pydantic model
    instruction: str
```

The framework recursively extracts `Image` objects from any nesting depth and serializes the remaining fields using Pydantic's `model_dump_json(exclude=...)`.

## License

This project is licensed under the MIT License. See the [LICENSE](../../LICENSE) file for details.
