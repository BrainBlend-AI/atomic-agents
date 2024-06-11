# Yelp Restaurant Finder Tool

[Atomic_agents Index](../../../README.md#atomic_agents-index) / [Atomic Agents](../../index.md#atomic-agents) / [Lib](../index.md#lib) / [Tools](./index.md#tools) / Yelp Restaurant Finder Tool

> Auto-generated documentation for [atomic_agents.lib.tools.yelp_restaurant_finder_tool](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py) module.

#### Attributes

- `table` - Create a table to display the results: Table(title='Yelp Search Results')


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

[Show source in yelp_restaurant_finder_tool.py:35](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L35)

#### Signature

```python
class PriceRange(Enum): ...
```



## YelpCategory

[Show source in yelp_restaurant_finder_tool.py:14](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L14)

#### Signature

```python
class YelpCategory(Enum): ...
```



## YelpSearchResultSchema

[Show source in yelp_restaurant_finder_tool.py:61](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L61)

#### Signature

```python
class YelpSearchResultSchema(BaseModel): ...
```



## YelpSearchTool

[Show source in yelp_restaurant_finder_tool.py:80](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L80)

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

[Show source in yelp_restaurant_finder_tool.py:104](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L104)

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

[Show source in yelp_restaurant_finder_tool.py:76](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L76)

#### Signature

```python
class YelpSearchToolConfig(BaseToolConfig): ...
```

#### See also

- [BaseToolConfig](./base.md#basetoolconfig)



## YelpSearchToolOutputSchema

[Show source in yelp_restaurant_finder_tool.py:70](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L70)

#### Signature

```python
class YelpSearchToolOutputSchema(BaseModel): ...
```



## YelpSearchToolSchema

[Show source in yelp_restaurant_finder_tool.py:41](../../../../../atomic_agents/lib/tools/yelp_restaurant_finder_tool.py#L41)

#### Signature

```python
class YelpSearchToolSchema(BaseModel): ...
```