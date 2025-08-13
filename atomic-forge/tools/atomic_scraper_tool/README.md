# Atomic Scraper Tool

Next-generation intelligent web scraping tool built with the Atomic Agents framework. This AI-powered tool provides advanced natural language processing, dynamic strategy generation, and ethical data extraction capabilities with unprecedented intelligence and ease of use.

> **🎯 Maximum Versatility**: Works perfectly as a **standalone CLI application**, **Python library**, or **orchestrated component** in multi-agent systems like atomic-cli and intelligent-web-scraper. Features innovative **model provider injection** for seamless integration across any execution context.

## 🚀 **Why Choose Atomic Scraper Tool?**

| Feature | Benefit | Use Case |
|---------|---------|----------|
| **🖥️ Standalone Ready** | Full-featured CLI with interactive interface | Data science, research, prototyping |
| **🔗 Orchestration Native** | Seamless integration with atomic-agents ecosystem | Production pipelines, multi-agent workflows |
| **🌐 Multi-Provider** | OpenAI, Anthropic, Azure, Google, local models | Any environment, any budget |
| **⚙️ Highly Configurable** | Extensive customization options | Enterprise deployments, specialized needs |
| **🛡️ Production Ready** | Ethical compliance, monitoring, error handling | Mission-critical applications |

## Features

### 🎯 **Core Capabilities**
- 🤖 **AI-Powered Planning**: Natural language scraping requests with intelligent strategy generation
- � **QDynamic Analysis**: Automatic website structure analysis and schema recipe generation
- �  **Quality Scoring**: Built-in data quality assessment and validation
- 🛡️ **Ethical Compliance**: Robots.txt respect, rate limiting, and privacy compliance
- 🧪 **Comprehensive Testing**: Mock website generation and integration testing
- 📈 **Performance Monitoring**: Built-in metrics and performance tracking

### 🔄 **Versatility & Integration**
- **🖥️ Standalone CLI**: Full-featured interactive application
- **🐍 Python Library**: Embeddable in custom applications
- **🔗 Orchestration Ready**: Seamless integration with atomic-cli and intelligent-web-scraper
- **🌐 Multi-Provider**: OpenAI, Anthropic, Azure, Google, and local models
- **⚙️ Configurable**: Extensive configuration options for any use case
- **🔧 Developer Friendly**: Rich debugging, monitoring, and testing tools

### 🎨 **Use Cases**

| Scenario | Mode | Benefits |
|----------|------|----------|
| **Data Science Research** | Standalone CLI | Interactive exploration, quick prototyping |
| **Production Data Pipeline** | Orchestrated | Consistent model usage, resource efficiency |
| **Custom Web Application** | Library Integration | Embedded scraping capabilities |
| **Multi-Agent Workflow** | Orchestrated | Coordinated with planning and analysis agents |
| **Enterprise Deployment** | Any | Configurable providers, compliance features |
| **Development & Testing** | Standalone + Debug | Rich debugging, mock websites, quality metrics |

## Quick Start

### Installation

```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -r requirements.txt
```

### Versatile Usage Patterns

#### 1. 🖥️ **Standalone CLI Application**

```bash
# Interactive mode with environment-based configuration
atomic-scraper

# With custom configuration
atomic-scraper --config my_config.json

# Debug mode for development
atomic-scraper --debug
```

#### 2. 🐍 **Python Library Integration**

```python
from atomic_scraper_tool.main import AtomicScraperApp

# Simple standalone usage
app = AtomicScraperApp()
app.run()

# With custom configuration
app = AtomicScraperApp(config_path="custom_config.json")
app.run()
```

#### 3. 🔗 **Orchestrated Integration**

```python
import instructor
import openai
from atomic_scraper_tool.main import create_orchestrated_app

# Create shared model provider
client = instructor.from_openai(openai.OpenAI())

# Create orchestrated instance
app = create_orchestrated_app(
    config={
        "scraper": {"max_results": 50, "quality_threshold": 80.0},
        "agent": {"model": "gpt-4", "temperature": 0.3}
    },
    client=client  # Injected model provider
)

# Use programmatically
result = app.process_scraping_request(
    request="Extract product information",
    url="https://example-store.com"
)
```

#### 4. 🌐 **Ecosystem Discovery**

```python
from atomic_scraper_tool.main import get_orchestration_metadata

# Get tool metadata for ecosystem integration
metadata = get_orchestration_metadata()
print(f"Tool: {metadata['name']}")
print(f"Supports orchestration: {metadata['supports_client_injection']}")
print(f"Available modes: {metadata['execution_modes']}")
```

### Environment Setup

The tool automatically detects available model providers:

```bash
# OpenAI (recommended)
export OPENAI_API_KEY="your-openai-key"

# Anthropic Claude
export ANTHROPIC_API_KEY="your-anthropic-key"

# Azure OpenAI
export AZURE_OPENAI_API_KEY="your-azure-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"

# Multiple providers supported simultaneously
```

### Programmatic Usage

```python
from atomic_scraper_tool.tools.atomic_scraper_tool import AtomicScraperTool
from atomic_scraper_tool.models.schema_models import SchemaRecipe

# Create scraper tool
scraper = AtomicScraperTool()

# Define scraping parameters
scraping_params = {
    'target_url': 'https://example.com/products',
    'strategy': {
        'scrape_type': 'list',
        'pagination_enabled': True,
        'max_pages': 5
    },
    'schema_recipe': {
        'fields': {
            'title': {'selector': 'h2.product-title', 'type': 'text'},
            'price': {'selector': '.price', 'type': 'text'},
            'rating': {'selector': '.rating', 'type': 'text'},
            'description': {'selector': '.description', 'type': 'text'}
        }
    },
    'max_results': 100
}

# Execute scraping
result = scraper.run(scraping_params)

# Access results
print(f"Scraped {result.results['total_scraped']} items")
for item in result.results['items']:
    print(f"Title: {item['title']}, Price: {item['price']}")
```

## Architecture

The Atomic Scraper Tool is built with a modular, next-generation architecture designed for **maximum versatility** across different execution contexts:

```
atomic_scraper_tool/
├── agents/                 # AI agents for planning and coordination
├── analysis/              # Website analysis and strategy generation
├── compliance/            # Ethical scraping compliance features
├── config/                # Configuration management
├── core/                  # Core interfaces and error handling
├── extraction/            # Content extraction and quality analysis
├── models/                # Data models and schemas
├── testing/               # Mock websites and test scenarios
├── tools/                 # Main scraper tool implementation
└── main.py               # Application entry point with orchestration support
```

### Key Architecture Design Insight: Model Provider Injection Pattern

**The Challenge**: Modern AI applications need to work in multiple execution contexts:
- **Standalone applications** with their own model providers
- **Orchestrated systems** where multiple agents share a common model provider
- **CLI tools** that coordinate multiple AI components
- **Web services** with centralized model management

**The Solution**: **Model Provider Injection at the Application Level**

Instead of hardcoding model providers in tools or agents, we inject them at the application boundary:

```python
# ❌ Traditional approach - hardcoded model provider
class ScrapingAgent:
    def __init__(self):
        self.client = openai.OpenAI()  # Hardcoded!

# ✅ Atomic Agents approach - injected model provider
class AtomicScraperApp:
    def __init__(self, client: Optional[instructor.Instructor] = None):
        self.injected_client = client  # Flexible injection point
```

**Benefits of This Pattern**:

1. **🔄 Context Adaptability**: Same tool works standalone or orchestrated
2. **⚡ Resource Efficiency**: Shared connections and rate limiting
3. **🎯 Consistency**: All agents use the same model configuration
4. **🔧 Testability**: Easy to inject mock clients for testing
5. **📈 Scalability**: Proper resource management in multi-agent scenarios
6. **🌐 Ecosystem Integration**: Seamless atomic-agents compatibility

### Execution Modes

The tool automatically detects and adapts to different execution contexts:

| Mode | Description | Model Provider | Use Case |
|------|-------------|----------------|----------|
| **Standalone** | Independent operation | Environment variables (OPENAI_API_KEY, etc.) | Direct CLI usage, development |
| **Orchestrated** | Coordinated with other agents | Injected by orchestrator | atomic-cli, intelligent-web-scraper |
| **Embedded** | Library integration | Programmatically provided | Custom applications, services |

### Multi-Provider Support

Supports all major AI providers through automatic detection:

- **OpenAI**: GPT-4, GPT-3.5-turbo, GPT-4-turbo
- **Anthropic**: Claude-3-opus, Claude-3-sonnet, Claude-3-haiku
- **Azure OpenAI**: Enterprise deployments
- **Google**: Gemini models
- **Local**: Ollama, custom endpoints

## Core Components

### 1. Scraper Planning Agent

The `AtomicScraperPlanningAgent` interprets natural language requests and generates scraping strategies:

```python
from atomic_scraper_tool.agents.scraper_planning_agent import AtomicScraperPlanningAgent

agent = AtomicScraperPlanningAgent()

request = {
    'url': 'https://example.com',
    'description': 'Extract product information including names, prices, and ratings'
}

strategy = agent.run(request)
print(strategy['reasoning'])
```

### 2. Website Analyzer

Automatically analyzes website structure and identifies content patterns:

```python
from atomic_scraper_tool.analysis.website_analyzer import WebsiteAnalyzer

analyzer = WebsiteAnalyzer()
analysis = analyzer.analyze_website('https://example.com')

print(f"Detected content type: {analysis.content_type}")
print(f"Pagination detected: {analysis.has_pagination}")
```

### 3. Schema Recipe Generator

Generates dynamic extraction schemas based on website analysis:

```python
from atomic_scraper_tool.analysis.schema_recipe_generator import SchemaRecipeGenerator

generator = SchemaRecipeGenerator()
schema = generator.generate_schema_recipe(analysis_result)

print(f"Generated {len(schema.fields)} extraction fields")
```

### 4. Content Extractor

Extracts structured data using CSS selectors and XPath:

```python
from atomic_scraper_tool.extraction.content_extractor import ContentExtractor

extractor = ContentExtractor()
extracted_data = extractor.extract_content(html, extraction_rules)

print(f"Extracted {len(extracted_data)} items")
```

### 5. Quality Analyzer

Assesses data quality and completeness:

```python
from atomic_scraper_tool.extraction.quality_analyzer import QualityAnalyzer

analyzer = QualityAnalyzer()
quality_score = analyzer.calculate_quality_score(extracted_data, schema_recipe)

print(f"Data quality score: {quality_score:.2f}")
```

## Compliance Features

### Robots.txt Compliance

```python
from atomic_scraper_tool.compliance.robots_parser import RobotsParser

parser = RobotsParser(user_agent="MyBot/1.0")

# Check if URL can be fetched
if parser.can_fetch('https://example.com/products'):
    print("URL is allowed by robots.txt")

# Get crawl delay
delay = parser.get_crawl_delay('https://example.com')
print(f"Recommended crawl delay: {delay} seconds")
```

### Rate Limiting

```python
from atomic_scraper_tool.compliance.rate_limiter import RateLimiter, RateLimitConfig

config = RateLimitConfig(
    default_delay=1.0,
    max_concurrent_requests=3,
    adaptive_delay_enabled=True
)

limiter = RateLimiter(config)

# Apply rate limiting
delay = limiter.wait_for_request('https://example.com/page1')
print(f"Applied delay: {delay} seconds")
```

### Privacy Compliance

```python
from atomic_scraper_tool.compliance.privacy_compliance import PrivacyComplianceChecker

checker = PrivacyComplianceChecker()

# Validate data collection
scraped_data = {'name': 'Product Name', 'price': '$19.99'}
is_compliant = checker.validate_data_collection('https://example.com', scraped_data)

if is_compliant:
    print("Data collection is compliant")
```

## Configuration

### Basic Configuration

```python
from atomic_scraper_tool.config.scraper_config import AtomicScraperConfig

config = AtomicScraperConfig(
    base_url="https://example.com",
    max_concurrent_requests=5,
    request_delay=1.0,
    timeout=30,
    user_agent="AtomicScraperTool/1.0"
)
```

### Advanced Configuration

```python
config = AtomicScraperConfig(
    # Request settings
    max_concurrent_requests=3,
    request_delay=2.0,
    timeout=60,
    max_retries=3,
    
    # Quality settings
    min_quality_score=0.7,
    enable_quality_filtering=True,
    
    # Compliance settings
    respect_robots_txt=True,
    enable_rate_limiting=True,
    privacy_compliance_enabled=True,
    
    # Output settings
    output_format="json",
    include_metadata=True,
    enable_data_validation=True
)
```

## Testing

### Mock Website Generation

```python
from atomic_scraper_tool.testing.mock_website import MockWebsiteGenerator

# Create mock e-commerce site
mock_site = MockWebsiteGenerator.create_ecommerce_site(num_products=50)

# Generate test pages
homepage = mock_site.generate_page("/")
product_page = mock_site.generate_page("/product/1")

# Get all available URLs
urls = mock_site.get_all_urls()
```

### Test Scenarios

```python
from atomic_scraper_tool.testing.test_scenarios import ScenarioGenerator, ScenarioType

generator = ScenarioGenerator()

# Generate test scenario
scenario = generator.generate_scenario(ScenarioType.BASIC_SCRAPING)

# Test with scenario
for url in scenario.test_urls:
    html = scenario.mock_website.generate_page(url)
    # Run validation rules
    for rule in scenario.validation_rules:
        assert rule(html)
```

## Error Handling

The tool provides comprehensive error handling:

```python
from atomic_scraper_tool.core.exceptions import ScrapingError

try:
    result = scraper.run(scraping_params)
except ScrapingError as e:
    print(f"Scraping error: {e.message}")
    print(f"Error type: {e.error_type}")
    print(f"URL: {e.url}")
    
    # Handle specific error types
    if e.error_type == "network_error":
        # Retry with different settings
        pass
    elif e.error_type == "parsing_error":
        # Adjust extraction rules
        pass
```

## Performance Optimization

### Concurrent Scraping

```python
import asyncio
from atomic_scraper_tool.tools.atomic_scraper_tool import AtomicScraperTool

async def scrape_multiple_urls(urls):
    scraper = AtomicScraperTool()
    tasks = []
    
    for url in urls:
        task = asyncio.create_task(scraper.run_async({
            'target_url': url,
            'strategy': {'scrape_type': 'detail'},
            'schema_recipe': schema
        }))
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results
```

### Memory Management

```python
# Enable streaming for large datasets
config = AtomicScraperConfig(
    enable_streaming=True,
    batch_size=100,
    memory_limit_mb=500
)

scraper = AtomicScraperTool(config=config)
```

## Best Practices

### 1. Respectful Scraping

- Always check robots.txt before scraping
- Use appropriate delays between requests
- Limit concurrent requests per domain
- Respect rate limiting headers

### 2. Data Quality

- Validate extracted data against expected schemas
- Implement quality thresholds
- Handle missing or malformed data gracefully
- Use data cleaning and normalization

### 3. Error Handling

- Implement retry logic for transient failures
- Log errors for debugging and monitoring
- Provide fallback strategies for critical failures
- Monitor success rates and performance metrics

### 4. Performance

- Use caching for repeated requests
- Implement connection pooling
- Monitor memory usage for large datasets
- Use streaming for processing large amounts of data

## API Reference

### Core Classes

#### AtomicScraperTool

Main scraping tool class.

**Methods:**
- `run(input_data)`: Execute scraping operation
- `validate_inputs(input_data)`: Validate input parameters
- `get_supported_formats()`: Get supported output formats

#### AtomicScraperPlanningAgent

AI agent for scraping strategy planning.

**Methods:**
- `run(request)`: Generate scraping strategy from natural language
- `parse_request(description)`: Parse user request
- `generate_strategy(analysis)`: Generate scraping strategy

#### WebsiteAnalyzer

Website structure analysis.

**Methods:**
- `analyze_website(url)`: Analyze website structure
- `detect_content_type(html)`: Detect content type
- `find_pagination(html)`: Detect pagination patterns

### Data Models

#### ScrapingStrategy

Defines scraping approach and parameters.

**Fields:**
- `scrape_type`: Type of scraping (list, detail, search, sitemap)
- `pagination_enabled`: Enable pagination handling
- `max_pages`: Maximum pages to scrape
- `selectors`: CSS selectors for content extraction

#### SchemaRecipe

Defines data extraction schema.

**Fields:**
- `fields`: Dictionary of field definitions
- `quality_weights`: Quality weights for fields
- `validation_rules`: Data validation rules

#### ScrapingResult

Contains scraping results and metadata.

**Fields:**
- `items`: Extracted data items
- `total_found`: Total items found
- `total_scraped`: Total items scraped
- `quality_score`: Overall quality score
- `execution_time`: Scraping execution time

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Orchestration & Integration

The Atomic Scraper Tool is designed for **maximum versatility** - it works perfectly as a standalone application or as part of larger AI ecosystems.

### 🎭 **Execution Modes Explained**

#### **Standalone Mode** 🖥️
Perfect for direct usage, development, and prototyping:

```bash
# Interactive CLI with full features
atomic-scraper

# Custom configuration
atomic-scraper --config production.json

# Development mode with debugging
atomic-scraper --debug
```

**Characteristics**:
- ✅ Uses environment variables for API keys
- ✅ Full interactive interface
- ✅ Independent operation
- ✅ Complete feature set

#### **Orchestrated Mode** 🔗
Seamless integration with multi-agent systems:

```python
import instructor
import openai
from atomic_scraper_tool.main import create_orchestrated_app

# Shared model provider across all agents
client = instructor.from_openai(openai.OpenAI())

# Create coordinated instance
app = create_orchestrated_app(
    config={
        "scraper": {"max_results": 100, "quality_threshold": 85.0},
        "agent": {"model": "gpt-4", "temperature": 0.2}
    },
    client=client  # Injected for consistency
)
```

**Characteristics**:
- ✅ Shared model provider with other agents
- ✅ Consistent configuration across ecosystem
- ✅ Resource efficiency and rate limiting
- ✅ Coordinated error handling

### 🌐 **Ecosystem Integration**

#### **With atomic-cli**
```bash
# atomic-cli automatically detects and integrates
atomic-cli add-tool atomic-scraper-tool
atomic-cli orchestrate "scrape product data from store.com"
```

#### **With intelligent-web-scraper**
```python
from intelligent_web_scraper import IntelligentScrapingOrchestrator
from atomic_scraper_tool.main import create_orchestrated_app

# Orchestrator creates shared client
orchestrator = IntelligentScrapingOrchestrator(config)
shared_client = orchestrator.client

# Inject into scraper tool
scraper = create_orchestrated_app(client=shared_client)
```

#### **Custom Integration**
```python
# Discover tool capabilities
from atomic_scraper_tool.main import get_orchestration_metadata

metadata = get_orchestration_metadata()
print(f"🔧 Tool: {metadata['name']}")
print(f"🎯 Category: {metadata['category']}")
print(f"🔗 Supports injection: {metadata['supports_client_injection']}")
print(f"🚀 Modes: {metadata['execution_modes']}")
```

### 🎯 **Integration Benefits**

| Benefit | Standalone | Orchestrated | Impact |
|---------|------------|--------------|---------|
| **Consistency** | ⚠️ Individual config | ✅ Shared configuration | Predictable behavior |
| **Efficiency** | ⚠️ Individual connections | ✅ Shared resources | Better performance |
| **Scalability** | ⚠️ Limited | ✅ Multi-agent coordination | Enterprise ready |
| **Monitoring** | ✅ Individual metrics | ✅ Centralized monitoring | Better observability |
| **Error Handling** | ✅ Local handling | ✅ Coordinated recovery | More robust |

### 🔧 **Advanced Integration Patterns**

#### **Multi-Provider Orchestration**
```python
# Different agents can use different providers
openai_client = instructor.from_openai(openai.OpenAI())
claude_client = instructor.from_anthropic(anthropic.Anthropic())

# Planning agent uses GPT-4
planning_app = create_orchestrated_app(
    config={"agent": {"model": "gpt-4"}},
    client=openai_client
)

# Extraction agent uses Claude
extraction_app = create_orchestrated_app(
    config={"agent": {"model": "claude-3-opus"}},
    client=claude_client
)
```

#### **Configuration Inheritance**
```python
# Base configuration
base_config = {
    "scraper": {"quality_threshold": 80.0, "respect_robots_txt": True},
    "agent": {"temperature": 0.3}
}

# Specialized configurations
ecommerce_config = {**base_config, "scraper": {**base_config["scraper"], "max_results": 200}}
news_config = {**base_config, "agent": {**base_config["agent"], "model": "gpt-4"}}

# Create specialized instances
ecommerce_scraper = create_orchestrated_app(config=ecommerce_config, client=client)
news_scraper = create_orchestrated_app(config=news_config, client=client)
```

This architecture ensures the tool is **truly versatile** - from simple CLI usage to complex multi-agent orchestrations.

## 📚 Documentation

- **[Architecture Guide](ARCHITECTURE.md)**: Deep dive into the model provider injection pattern and design principles
- **[Problem Solving Guide](README.md#problem-solving)**: Common issues and solutions
- **[API Reference](README.md#api-reference)**: Complete API documentation
- **[Contributing Guide](CONTRIBUTING.md)**: How to contribute to the project

## Support

For questions, issues, or contributions, please visit our GitHub repository or contact the development team.