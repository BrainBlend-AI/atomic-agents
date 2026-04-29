# arXiv Search Tool

## Overview
Searches arXiv for academic papers via the free public API and returns each paper's title, authors, abstract, dates, categories, and links to the abstract page and the PDF. No API key required.

## Prerequisites and Dependencies
- Python 3.12 or later
- `atomic-agents`
- `pydantic`
- `aiohttp`

## Installation
1. Use the Atomic Assembler CLI: run `atomic` and pick `arxiv_search`.
2. Or copy the `tool/` folder directly into your project.

## Input & Output Structure

### Input Schema
- `queries` (list[str]): plain keywords or arXiv field-prefixed expressions (`ti:`, `au:`, `abs:`, `cat:`, `id:`, `all:`).
- `max_results_per_query` (int): 1–50 (default 5).
- `sort_by` (str): `relevance`, `lastUpdatedDate`, or `submittedDate` (default `relevance`).
- `sort_order` (str): `ascending` or `descending` (default `descending`).
- `category` (str, optional): arXiv category filter (e.g. `cs.AI`).

### Output Schema
A list of `ArxivPaper` items. Each has `arxiv_id`, `title`, `summary`, `authors`, `published`, `updated`, `categories`, `primary_category`, `pdf_url`, `abs_url`, optional `comment` and `journal_ref`.

## Usage

```python
from tool.arxiv_search import ArxivSearchTool, ArxivSearchToolInputSchema

tool = ArxivSearchTool()

output = tool.run(ArxivSearchToolInputSchema(
    queries=["retrieval augmented generation"],
    max_results_per_query=3,
    category="cs.AI",
))

for paper in output.results:
    print(paper.arxiv_id, "-", paper.title)
    print(paper.pdf_url)
```

## Contributing
PRs welcome — see the main repo `CONTRIBUTING.md`.

## License
Same as the main Atomic Agents project.
