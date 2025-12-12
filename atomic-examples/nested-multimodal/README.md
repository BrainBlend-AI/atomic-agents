# Nested Multimodal Content Example

Analyze multiple images (or PDFs/audio) in a single request using nested schemas.

## What This Does

Pass a **list of documents** - each containing an image plus metadata - to an agent that analyzes them all and provides a comparative summary.

```python
class ImageDocument(BaseIOSchema):
    image: Image = Field(...)
    owner: str = Field(...)
    category: str = Field(...)

class Input(BaseIOSchema):
    documents: list[ImageDocument] = Field(...)  # Multiple images with metadata
    query: str = Field(...)

# Analyze multiple images at once
result = agent.run(Input(
    documents=[doc1, doc2, doc3],
    query="Compare these images"
))
```

## Setup

```bash
cd atomic-examples/nested-multimodal
uv sync
```

Set your API key in `.env`:
```
OPENAI_API_KEY=your_key_here
# or
GEMINI_API_KEY=your_key_here
```

## Run

```bash
uv run python nested_multimodal/main.py
```

## Example Output

```
Using OpenAI GPT-5.1

Creating nested document structure...
  - Document 1: Image owned by 'Marketing Team', category 'photo'
  - Document 2: Image owned by 'Content Team', category 'photo'

============================================================
ANALYSIS RESULTS
============================================================

Image 1:
  Owner: Marketing Team
  Description: A black-and-white mountain valley with dramatic lighting...
  Dominant Colors: black, white, gray
  Key Elements: mountain slopes, valley, diagonal light beam

Image 2:
  Owner: Content Team
  Description: Layered blue mountain ridges receding into distance...
  Dominant Colors: various blues, soft white haze
  Key Elements: overlapping ridges, atmospheric haze

Comparative Summary:
  Both images depict mountainous landscapes with atmospheric depth...
  The first is high-contrast black-and-white, the second uses blue tones...

SUCCESS: Nested multimodal content handled correctly!
```
