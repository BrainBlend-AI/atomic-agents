# Nested Multimodal Content Example

This example demonstrates the support for **nested multimodal content** in Atomic Agents, as implemented for [GitHub Issue #141](https://github.com/BrainBlend-AI/atomic-agents/issues/141).

## The Problem (Issue #141)

Previously, `ChatHistory` only detected multimodal content (Image, PDF, Audio) at the **top level** of input schemas. When multimodal content was nested within other schemas, it was incorrectly serialized with `json.dumps`, causing issues.

For example, this structure would NOT work correctly:

```python
class Document(BaseIOSchema):
    pdf: PDF = Field(...)  # Nested multimodal content
    owner: str = Field(...)

class InputSchema(BaseIOSchema):
    documents: list[Document] = Field(...)  # List of nested schemas with PDFs
```

## The Solution

The `ChatHistory.get_history()` method now **recursively** detects and extracts multimodal content from any depth of nested schemas:

1. `_contains_multimodal(obj)` - Recursively checks for multimodal content
2. `_extract_multimodal_objects(obj)` - Recursively extracts all multimodal objects
3. `_build_non_multimodal_dict(obj)` - Builds JSON excluding multimodal content

## What This Example Demonstrates

This example creates:
- A `Document` schema containing a `PDF` field AND metadata (owner, type)
- A `NestedMultimodalInput` schema containing a **list** of `Document` objects
- An agent that processes all nested PDFs and provides comparative analysis

This is the exact scenario that was broken before Issue #141 was fixed.

## Prerequisites

1. **Google AI API Key**: This example uses Google's Gemini model for multimodal processing.

   Set your API key in `.env`:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

2. **Python 3.12+**

## Installation

From the monorepo root:

```bash
cd atomic-examples/nested-multimodal
uv sync
```

## Running the Example

```bash
uv run python nested_multimodal/main.py
```

## Expected Output

```
============================================================
Nested Multimodal Content Example (Issue #141)
============================================================

Using test PDF: .../test_media/pdf_sample.pdf

Creating nested document structure...
  - Document 1: PDF owned by 'Legal Department', type 'contract'
  - Document 2: PDF owned by 'Finance Team', type 'report'

Sending nested multimodal content to agent...
(Previously this would fail due to incorrect JSON serialization)

============================================================
ANALYSIS RESULTS
============================================================

Document 1:
  Owner: Legal Department
  Type: contract
  Title: [extracted title]
  Pages: [page count]
  Summary: [brief summary]

Document 2:
  Owner: Finance Team
  Type: report
  Title: [extracted title]
  Pages: [page count]
  Summary: [brief summary]

Comparative Summary:
  [AI-generated comparison based on the query]

============================================================
SUCCESS: Nested multimodal content handled correctly!
============================================================
```

## Key Code Patterns

### Defining Nested Multimodal Schemas

```python
from instructor.multimodal import PDF

class Document(BaseIOSchema):
    """Document with nested PDF content."""
    pdf: PDF = Field(..., description="The PDF content")
    owner: str = Field(..., description="Document owner")

class InputSchema(BaseIOSchema):
    """Input with list of nested documents."""
    documents: List[Document] = Field(..., description="Documents to analyze")
    query: str = Field(..., description="Analysis query")
```

### Creating Nested Input

```python
doc1 = Document(pdf=PDF.from_path("doc1.pdf"), owner="Alice")
doc2 = Document(pdf=PDF.from_path("doc2.pdf"), owner="Bob")

input_data = InputSchema(
    documents=[doc1, doc2],
    query="Compare these documents"
)

# This now works correctly!
result = agent.run(input_data)
```

## Related Issues

- [Issue #141: AgentMemory: support nested multimodal data](https://github.com/BrainBlend-AI/atomic-agents/issues/141)
- [PR #137: Improve handling of multi-modal content in AgentMemory](https://github.com/BrainBlend-AI/atomic-agents/pull/137)
