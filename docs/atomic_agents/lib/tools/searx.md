# Searx

[Atomic_agents_redux Index](../../../README.md#atomic_agents_redux-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Creating a New Tool](./index.md#creating-a-new-tool) / Searx

> Auto-generated documentation for [atomic_agents.lib.tools.searx](../../../../atomic_agents/lib/tools/searx.py) module.

#### Attributes

- `client` - Initialize the client outside: instructor.from_openai(openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'), base_url=os.getenv('OPENAI_BASE_URL')))

- `result` - Extract structured data from natural language: client.chat.completions.create(model='gpt-3.5-turbo', response_model=SearxNGSearchTool.input_schema, messages=[{'role': 'user', 'content': 'Search for the latest PC gaming news of May 2024 using 3 different queries.'}])

- `output` - Print the result: SearxNGSearchTool(max_results=15).run(result)


- [Searx](#searx)
  - [SearxNGSearchResultSchema](#searxngsearchresultschema)
  - [SearxNGSearchTool](#searxngsearchtool)
    - [SearxNGSearchTool().run](#searxngsearchtool()run)
  - [SearxNGSearchToolOutputSchema](#searxngsearchtooloutputschema)
  - [SearxNGSearchToolSchema](#searxngsearchtoolschema)

## SearxNGSearchResultSchema

[Show source in searx.py:29](../../../../atomic_agents/lib/tools/searx.py#L29)

#### Signature

```python
class SearxNGSearchResultSchema(BaseModel): ...
```



## SearxNGSearchTool

[Show source in searx.py:41](../../../../atomic_agents/lib/tools/searx.py#L41)

Tool for performing searches on SearxNG based on the provided queries and category.

#### Attributes

- `input_schema` *SearxNGSearchToolSchema* - The schema for the input data.
- `output_schema` *SearxNGSearchToolOutputSchema* - The schema for the output data.
- `max_results` *int* - The maximum number of search results to return.

#### Signature

```python
class SearxNGSearchTool(BaseTool):
    def __init__(self, max_results: int = 10, *args, **kwargs): ...
```

#### See also

- [BaseTool](./base.md#basetool)

### SearxNGSearchTool().run

[Show source in searx.py:65](../../../../atomic_agents/lib/tools/searx.py#L65)

Runs the SearxNGSearchTool with the given parameters.

#### Arguments

- `params` *SearxNGSearchToolSchema* - The input parameters for the tool, adhering to the input schema.
- `max_results` *Optional[int]* - The maximum number of search results to return.

#### Returns

- [SearxNGSearchToolOutputSchema](#searxngsearchtooloutputschema) - The output of the tool, adhering to the output schema.

#### Raises

- `ValueError` - If the SEARXNG_BASE_URL environment variable is not set.
- `Exception` - If the request to SearxNG fails.

#### Signature

```python
def run(
    self, params: SearxNGSearchToolSchema, max_results: Optional[int] = None
) -> SearxNGSearchToolOutputSchema: ...
```

#### See also

- [SearxNGSearchToolOutputSchema](#searxngsearchtooloutputschema)
- [SearxNGSearchToolSchema](#searxngsearchtoolschema)



## SearxNGSearchToolOutputSchema

[Show source in searx.py:35](../../../../atomic_agents/lib/tools/searx.py#L35)

#### Signature

```python
class SearxNGSearchToolOutputSchema(BaseModel): ...
```



## SearxNGSearchToolSchema

[Show source in searx.py:14](../../../../atomic_agents/lib/tools/searx.py#L14)

#### Signature

```python
class SearxNGSearchToolSchema(BaseModel): ...
```