# ContentScrapingTool

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Tools](./index.md#tools) / ContentScrapingTool

> Auto-generated documentation for [atomic_agents.lib.tools.content_scraping_tool](../../../../../atomic_agents/lib/tools/content_scraping_tool.py) module.

#### Attributes

- `result` - ################
  TEST WEB PAGE #
  ################: client.chat.completions.create(model='gpt-3.5-turbo', response_model=ContentScrapingTool.input_schema, messages=[{'role': 'user', 'content': 'Scrape the content of https://example.com'}])

- `result` - ###############
  TEST PDF URL #
  ###############: client.chat.completions.create(model='gpt-3.5-turbo', response_model=ContentScrapingTool.input_schema, messages=[{'role': 'user', 'content': 'Scrape the content of https://pdfobject.com/pdf/sample.pdf'}])


- [ContentScrapingTool](#contentscrapingtool)
  - [ContentScrapingResultSchema](#contentscrapingresultschema)
  - [ContentScrapingTool](#contentscrapingtool-1)
    - [ContentScrapingTool().run](#contentscrapingtool()run)
  - [ContentScrapingToolConfig](#contentscrapingtoolconfig)
  - [ContentScrapingToolOutputSchema](#contentscrapingtooloutputschema)
  - [ContentScrapingToolSchema](#contentscrapingtoolschema)

## ContentScrapingResultSchema

[Show source in content_scraping_tool.py:30](../../../../../atomic_agents/lib/tools/content_scraping_tool.py#L30)

#### Signature

```python
class ContentScrapingResultSchema(BaseModel): ...
```



## ContentScrapingTool

[Show source in content_scraping_tool.py:43](../../../../../atomic_agents/lib/tools/content_scraping_tool.py#L43)

Tool for scraping web pages or PDFs and converting content to markdown.

#### Attributes

- `input_schema` *ContentScrapingToolSchema* - The schema for the input data.
- `output_schema` *ContentScrapingToolOutputSchema* - The schema for the output data.

#### Signature

```python
class ContentScrapingTool(BaseTool):
    def __init__(
        self, config: ContentScrapingToolConfig = ContentScrapingToolConfig()
    ): ...
```

#### See also

- [BaseTool](./base.md#basetool)
- [ContentScrapingToolConfig](#contentscrapingtoolconfig)

### ContentScrapingTool().run

[Show source in content_scraping_tool.py:63](../../../../../atomic_agents/lib/tools/content_scraping_tool.py#L63)

Runs the ContentScrapingTool with the given parameters.

#### Arguments

- `params` *ContentScrapingToolSchema* - The input parameters for the tool, adhering to the input schema.

#### Returns

- [ContentScrapingToolOutputSchema](#contentscrapingtooloutputschema) - The output of the tool, adhering to the output schema.

#### Signature

```python
def run(self, params: ContentScrapingToolSchema) -> ContentScrapingToolOutputSchema: ...
```

#### See also

- [ContentScrapingToolOutputSchema](#contentscrapingtooloutputschema)
- [ContentScrapingToolSchema](#contentscrapingtoolschema)



## ContentScrapingToolConfig

[Show source in content_scraping_tool.py:40](../../../../../atomic_agents/lib/tools/content_scraping_tool.py#L40)

#### Signature

```python
class ContentScrapingToolConfig(BaseToolConfig): ...
```

#### See also

- [BaseToolConfig](./base.md#basetoolconfig)



## ContentScrapingToolOutputSchema

[Show source in content_scraping_tool.py:34](../../../../../atomic_agents/lib/tools/content_scraping_tool.py#L34)

#### Signature

```python
class ContentScrapingToolOutputSchema(BaseModel): ...
```



## ContentScrapingToolSchema

[Show source in content_scraping_tool.py:16](../../../../../atomic_agents/lib/tools/content_scraping_tool.py#L16)

#### Signature

```python
class ContentScrapingToolSchema(BaseModel): ...
```