# Web Scraping Tool

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Tools](./index.md#tools) / Web Scraping Tool

> Auto-generated documentation for [atomic_agents.lib.tools.web_scraping_tool](../../../../atomic_agents/lib/tools/web_scraping_tool.py) module.

#### Attributes

- `client` - Initialize the client outside: instructor.from_openai(openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'), base_url=os.getenv('OPENAI_BASE_URL')))

- `result` - Extract from webpage: client.chat.completions.create(model='gpt-3.5-turbo', response_model=ContentScrapingTool.input_schema, messages=[{'role': 'user', 'content': 'Scrape the content of https://example.com'}])

- `output` - Print the result: ContentScrapingTool().run(result)

- `result` - Extract from PDF: client.chat.completions.create(model='gpt-3.5-turbo', response_model=ContentScrapingTool.input_schema, messages=[{'role': 'user', 'content': 'Scrape the content of https://pdfobject.com/pdf/sample.pdf'}])

- `output` - Print the result: ContentScrapingTool().run(result)


- [Web Scraping Tool](#web-scraping-tool)
  - [ContentScrapingResultSchema](#contentscrapingresultschema)
  - [ContentScrapingTool](#contentscrapingtool)
    - [ContentScrapingTool().run](#contentscrapingtool()run)
  - [ContentScrapingToolOutputSchema](#contentscrapingtooloutputschema)
  - [ContentScrapingToolSchema](#contentscrapingtoolschema)

## ContentScrapingResultSchema

[Show source in web_scraping_tool.py:30](../../../../atomic_agents/lib/tools/web_scraping_tool.py#L30)

#### Signature

```python
class ContentScrapingResultSchema(BaseModel): ...
```



## ContentScrapingTool

[Show source in web_scraping_tool.py:40](../../../../atomic_agents/lib/tools/web_scraping_tool.py#L40)

Tool for scraping web pages or PDFs and converting content to markdown.

#### Attributes

- `input_schema` *ContentScrapingToolSchema* - The schema for the input data.
- `output_schema` *ContentScrapingToolOutputSchema* - The schema for the output data.

#### Signature

```python
class ContentScrapingTool(BaseTool):
    def __init__(self, *args, **kwargs): ...
```

#### See also

- [BaseTool](./base.md#basetool)

### ContentScrapingTool().run

[Show source in web_scraping_tool.py:61](../../../../atomic_agents/lib/tools/web_scraping_tool.py#L61)

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



## ContentScrapingToolOutputSchema

[Show source in web_scraping_tool.py:34](../../../../atomic_agents/lib/tools/web_scraping_tool.py#L34)

#### Signature

```python
class ContentScrapingToolOutputSchema(BaseModel): ...
```



## ContentScrapingToolSchema

[Show source in web_scraping_tool.py:16](../../../../atomic_agents/lib/tools/web_scraping_tool.py#L16)

#### Signature

```python
class ContentScrapingToolSchema(BaseModel): ...
```