# Atomic Scraper Tool

Next-generation intelligent web scraping tool built with the Atomic Agents framework. This AI-powered tool provides advanced natural language processing, dynamic strategy generation, and ethical data extraction capabilities with unprecedented intelligence and ease of use.

## Features

- **AI-Powered Planning**: Natural language scraping requests with intelligent strategy generation.
- **Dynamic Analysis**: Automatic website structure analysis and schema recipe generation.
- **Quality Scoring**: Built-in data quality assessment and validation.
- **Ethical Compliance**: Robots.txt respect, rate limiting, and privacy compliance.
- **Comprehensive Testing**: Mock website generation and integration testing.
- **Performance Monitoring**: Built-in metrics and performance tracking.

## Usage

The `AtomicScraperTool` can be used programmatically within your Python applications.

### Initialization

To get started, instantiate the `AtomicScraperTool` with an optional configuration object:

```python
from atomic_scraper_tool.tools.atomic_scraper_tool import AtomicScraperTool
from atomic_scraper_tool.config.scraper_config import AtomicScraperConfig

# Initialize with default configuration
scraper_tool = AtomicScraperTool()

# Or with a custom configuration
custom_config = AtomicScraperConfig(
    base_url="https://my-target-website.com",
    request_delay=2.0,
    timeout=60,
    min_quality_score=75.0
)
scraper_tool_with_config = AtomicScraperTool(config=custom_config)
```

### Running the Tool

The `run` method executes the scraping operation. It takes an `AtomicScraperInputSchema` object as input, which defines the target URL, scraping strategy, and schema recipe.

```python
from atomic_scraper_tool.tools.atomic_scraper_tool import AtomicScraperInputSchema

input_data = AtomicScraperInputSchema(
    target_url="https://example.com/products",
    strategy={
        "scrape_type": "list",
        "target_selectors": [".product-item"],
        "pagination_strategy": "next_link",
        "max_pages": 5
    },
    schema_recipe={
        "name": "product_recipe",
        "fields": {
            "product_name": {"field_type": "string", "extraction_selector": ".product-title"},
            "price": {"field_type": "string", "extraction_selector": ".price"}
        }
    },
    max_results=50
)

result = scraper_tool.run(input_data)

# Process the results
if result.results['items']:
    for item in result.results['items']:
        print(f"Product: {item['data']['product_name']}, Price: {item['data']['price']}")
```

## Configuration

The `AtomicScraperTool` is configured using the `AtomicScraperConfig` class. This class provides a wide range of options to customize the scraper's behavior.

### Key Configuration Parameters

- `base_url` (str): The base URL for relative link resolution.
- `request_delay` (float): The delay in seconds between requests to the same domain.
- `timeout` (int): The timeout for HTTP requests.
- `max_retries` (int): The maximum number of retries for failed requests.
- `user_agent` (str): The User-Agent string to use for requests.
- `min_quality_score` (float): The minimum quality score for an item to be included in the results.
- `respect_robots_txt` (bool): Whether to respect the `robots.txt` file of the target website.
- `enable_rate_limiting` (bool): Whether to enable automatic rate limiting.

## Error Handling

The tool includes a robust error handling mechanism and defines a set of custom exceptions to handle various scraping-related issues.

### Custom Exceptions

- `ScrapingError`: The base exception for all scraping-related errors.
- `NetworkError`: Raised for network-related issues, such as connection errors or timeouts.
- `ParsingError`: Raised when there is an error parsing the HTML content of a page.
- `QualityError`: Raised when the quality of the scraped data falls below the configured threshold.

### Error Handling in Practice

When using the tool, it's recommended to wrap the `run` method in a `try...except` block to handle potential exceptions:

```python
from atomic_scraper_tool.core.exceptions import ScrapingError

try:
    result = scraper_tool.run(input_data)
except ScrapingError as e:
    print(f"An error occurred during scraping: {e}")
    # Implement your error handling logic here
```
