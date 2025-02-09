# Tools Guide

Atomic Agents provides a collection of tools through the Atomic Forge that extend agent capabilities.

## Installing Tools

Tools are managed using the Atomic Assembler CLI:

```bash
# Install a specific tool
atomic-assembler install calculator

# List available tools
atomic-assembler list

# Update installed tools
atomic-assembler update
```

## Available Tools

### Calculator

A tool for performing mathematical calculations:

```python
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig

agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        tools=["calculator"]
    )
)

# The agent can now perform calculations
response = agent.run({
    "chat_message": "What is the square root of 144 plus 50?"
})
```

### SearxNG Search

A privacy-focused web search tool:

```python
# Configure with your SearxNG instance
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        tools=["searxng_search"],
        tool_configs={
            "searxng_search": {
                "instance_url": "https://your-searxng-instance.com"
            }
        }
    )
)
```

### Tavily Search

An AI-optimized search engine:

```python
import os

# Set your Tavily API key
os.environ["TAVILY_API_KEY"] = "your-api-key"

agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        tools=["tavily_search"]
    )
)
```

### YouTube Transcript Scraper

Extract transcripts from YouTube videos:

```python
import os

# Set your YouTube API key
os.environ["YOUTUBE_API_KEY"] = "your-api-key"

agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        tools=["youtube_transcript"]
    )
)

# The agent can now analyze YouTube videos
response = agent.run({
    "chat_message": "Summarize this video: https://youtube.com/watch?v=..."
})
```

### Webpage Scraper

Extract content from web pages:

```python
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",
        tools=["webpage_scraper"]
    )
)

# The agent can now analyze web pages
response = agent.run({
    "chat_message": "What are the main points from this article: https://..."
})
```

## Creating Custom Tools

You can create your own tools by following these steps:

### 1. Create Tool Structure

Create a new directory with the required files:

```
my_tool/
├── __init__.py
├── README.md
├── pyproject.toml
└── my_tool/
    ├── __init__.py
    └── tool.py
```

### 2. Implement Tool Logic

Create your tool implementation:

```python
from pydantic import BaseModel
from atomic_agents.lib.tools import BaseTool

class MyToolInputs(BaseModel):
    param1: str
    param2: int

class MyToolOutputs(BaseModel):
    result: str

class MyTool(BaseTool):
    name = "my_tool"
    description = "Description of what my tool does"
    inputs_schema = MyToolInputs
    outputs_schema = MyToolOutputs

    def run(self, inputs: MyToolInputs) -> MyToolOutputs:
        # Implement your tool logic here
        result = f"Processed {inputs.param1} {inputs.param2} times"
        return MyToolOutputs(result=result)
```

### 3. Configure Package

Create a pyproject.toml:

```toml
[tool.poetry]
name = "my-tool"
version = "0.1.0"
description = "My custom tool for Atomic Agents"
authors = ["Your Name <your.email@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
atomic-agents = "^0.1.0"
```

### 4. Document Usage

Create a README.md with:

* Installation instructions
* Configuration requirements
* Usage examples
* Any environment variables needed

## Best Practices

### 1. Error Handling

* Implement proper error handling in tools
* Return meaningful error messages
* Handle rate limits and retries

### 2. Configuration

* Use environment variables for sensitive data
* Make configuration flexible but with sensible defaults
* Document all configuration options

### 3. Testing

* Write unit tests for your tools
* Include integration tests if applicable
* Test error cases and edge conditions

### 4. Documentation

* Keep README up to date
* Include example code
* Document any breaking changes

## Next Steps

* Check out the [example projects](../examples/index.md)
* Learn about [advanced usage patterns](advanced_usage.md)
* Contribute your own tools to the [Atomic Forge](../contributing.md)
