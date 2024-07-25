# ContentScrapingTool

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Tools](./index.md#tools) / ContentScrapingTool

> Auto-generated documentation for [atomic_agents.lib.tools.content_scraping_tool](../../../../../atomic_agents/lib/tools/content_scraping_tool.py) module.

#### Attributes

- `result` - ################
  TEST WEB PAGE #
  ################: client.chat.completions.create(model='gpt-3.5-turbo', response_model=ContentScrapingTool.input_schema, messages=[{'role': 'user', 'content': 'Scrape the content of https://brainblendai.com'}])

- `result` - ###############
  TEST PDF URL #
  ###############: client.chat.completions.create(model='gpt-3.5-turbo', response_model=ContentScrapingTool.input_schema, messages=[{'role': 'user', 'content': 'Scrape the content of https://pdfobject.com/pdf/sample.pdf'}])


- [ContentScrapingTool](#contentscrapingtool)
  - [ContentScrapingTool](#contentscrapingtool-1)
    - [ContentScrapingTool().run](#contentscrapingtool()run)
  - [ContentScrapingToolConfig](#contentscrapingtoolconfig)
  - [ContentScrapingToolInputSchema](#contentscrapingtoolinputschema)
  - [ContentScrapingToolOutputSchema](#contentscrapingtooloutputschema)

## ContentScrapingTool

[Show source in content_scraping_tool.py:50](../../../../../atomic_agents/lib/tools/content_scraping_tool.py#L50)

Tool for scraping web pages or PDFs and converting content to markdown.

#### Attributes

- `input_schema` *ContentScrapingToolInputSchema* - The schema for the input data.
- `output_schema` *ContentScrapingToolOutputSchema* - The schema for the output data.

#### Signature

```python
class ContentScrapingTool(BaseTool):
    def __init__(
        self, config: ContentScrapingToolConfig = ContentScrapingToolConfig()
    ): ...
```

#### See also

- [BaseTool](./base_tool.md#basetool)
- [ContentScrapingToolConfig](#contentscrapingtoolconfig)

### ContentScrapingTool().run

[Show source in content_scraping_tool.py:71](../../../../../atomic_agents/lib/tools/content_scraping_tool.py#L71)

Runs the ContentScrapingTool with the given parameters.

#### Arguments

- `params` *ContentScrapingToolInputSchema* - The input parameters for the tool, adhering to the input schema.

#### Returns

- [ContentScrapingToolOutputSchema](#contentscrapingtooloutputschema) - The output of the tool, adhering to the output schema.

#### Signature

```python
def run(
    self, params: ContentScrapingToolInputSchema
) -> ContentScrapingToolOutputSchema: ...
```

#### See also

- [ContentScrapingToolInputSchema](#contentscrapingtoolinputschema)
- [ContentScrapingToolOutputSchema](#contentscrapingtooloutputschema)



## ContentScrapingToolConfig

[Show source in content_scraping_tool.py:46](../../../../../atomic_agents/lib/tools/content_scraping_tool.py#L46)

#### Signature

```python
class ContentScrapingToolConfig(BaseToolConfig): ...
```

#### See also

- [BaseToolConfig](./base_tool.md#basetoolconfig)



## ContentScrapingToolInputSchema

[Show source in content_scraping_tool.py:21](../../../../../atomic_agents/lib/tools/content_scraping_tool.py#L21)

#### Signature

```python
class ContentScrapingToolInputSchema(BaseIOSchema): ...
```

#### See also

- [BaseIOSchema](../../agents/base_agent.md#baseioschema)



## ContentScrapingToolOutputSchema

[Show source in content_scraping_tool.py:38](../../../../../atomic_agents/lib/tools/content_scraping_tool.py#L38)

#### Signature

```python
class ContentScrapingToolOutputSchema(BaseIOSchema): ...
```

#### See also

- [BaseIOSchema](../../agents/base_agent.md#baseioschema)