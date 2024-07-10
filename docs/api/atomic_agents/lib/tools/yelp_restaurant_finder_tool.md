# Yelp Restaurant Finder Tool

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Tools](./index.md#tools) / Yelp Restaurant Finder Tool

> Auto-generated documentation for [atomic_agents.lib.tools.yelp_restaurant_finder_tool](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py) module.

- [Yelp Restaurant Finder Tool](#yelp-restaurant-finder-tool)
  - [PriceRange](#pricerange)
  - [YelpCategory](#yelpcategory)
  - [YelpSearchResultSchema](#yelpsearchresultschema)
  - [YelpSearchTool](#yelpsearchtool)
    - [YelpSearchTool().run](#yelpsearchtool()run)
  - [YelpSearchToolConfig](#yelpsearchtoolconfig)
  - [YelpSearchToolOutputSchema](#yelpsearchtooloutputschema)
  - [YelpSearchToolSchema](#yelpsearchtoolschema)

## PriceRange

[Show source in yelp_restaurant_finder_tool.py:36](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L36)

#### Signature

```python
class PriceRange(Enum): ...
```



## YelpCategory

[Show source in yelp_restaurant_finder_tool.py:15](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L15)

#### Signature

```python
class YelpCategory(Enum): ...
```



## YelpSearchResultSchema

[Show source in yelp_restaurant_finder_tool.py:62](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L62)

#### Signature

```python
class YelpSearchResultSchema(BaseAgentIO): ...
```

#### See also

- [BaseAgentIO](../../agents/base_agent.md#baseagentio)



## YelpSearchTool

[Show source in yelp_restaurant_finder_tool.py:89](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L89)

Tool for performing searches using the Yelp API based on the provided queries.

#### Attributes

- `input_schema` *YelpSearchToolSchema* - The schema for the input data.
- `output_schema` *YelpSearchToolOutputSchema* - The schema for the output data.
- `api_key` *str* - The API key for the Yelp API.
- `max_results` *int* - The maximum number of search results to return.

#### Signature

```python
class YelpSearchTool(BaseTool):
    def __init__(self, config: YelpSearchToolConfig = YelpSearchToolConfig()): ...
```

#### See also

- [BaseTool](./base.md#basetool)
- [YelpSearchToolConfig](#yelpsearchtoolconfig)

### YelpSearchTool().run

[Show source in yelp_restaurant_finder_tool.py:113](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L113)

Runs the YelpSearchTool with the given parameters.

#### Arguments

- `params` *YelpSearchToolSchema* - The input parameters for the tool, adhering to the input schema.
- `max_results` *Optional[int]* - The maximum number of search results to return.

#### Returns

- [YelpSearchToolOutputSchema](#yelpsearchtooloutputschema) - The output of the tool, adhering to the output schema.

#### Raises

- `ValueError` - If the API key is not provided.
- `Exception` - If the request to Yelp API fails.

#### Signature

```python
def run(self, params: YelpSearchToolSchema) -> YelpSearchToolOutputSchema: ...
```

#### See also

- [YelpSearchToolOutputSchema](#yelpsearchtooloutputschema)
- [YelpSearchToolSchema](#yelpsearchtoolschema)



## YelpSearchToolConfig

[Show source in yelp_restaurant_finder_tool.py:85](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L85)

#### Signature

```python
class YelpSearchToolConfig(BaseToolConfig): ...
```

#### See also

- [BaseToolConfig](./base.md#basetoolconfig)



## YelpSearchToolOutputSchema

[Show source in yelp_restaurant_finder_tool.py:71](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L71)

#### Signature

```python
class YelpSearchToolOutputSchema(BaseAgentIO): ...
```

#### See also

- [BaseAgentIO](../../agents/base_agent.md#baseagentio)



## YelpSearchToolSchema

[Show source in yelp_restaurant_finder_tool.py:42](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L42)

#### Signature

```python
class YelpSearchToolSchema(BaseAgentIO): ...
```

#### See also

- [BaseAgentIO](../../agents/base_agent.md#baseagentio)