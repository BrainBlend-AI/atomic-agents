# Tools Guide

Atomic Agents uses a unique approach to tools through the **Atomic Forge** system. Rather than bundling all tools into a single package, tools are designed to be standalone, modular components that you can download and integrate into your project as needed.

## Philosophy

The Atomic Forge approach provides several key benefits:

1. **Full Control**: You have complete ownership and control over each tool you download. Want to modify a tool's behavior? You can change it without impacting other users.
2. **Dependency Management**: Since tools live in your codebase, you have better control over dependencies.
3. **Lightweight**: Download only the tools you need, avoiding unnecessary dependencies. For example, you don't need Sympy if you're not using the Calculator tool.

## Available Tools

The Atomic Forge includes several pre-built tools:

- **Calculator**: Perform mathematical calculations
- **SearXNG Search**: Search the web using SearXNG
- **Tavily Search**: AI-powered web search
- **YouTube Transcript Scraper**: Extract transcripts from YouTube videos
- **Webpage Scraper**: Extract content from web pages

## Using Tools

### 1. Download Tools

Use the Atomic Assembler CLI to download tools:

```bash
atomic
```

This will present a menu where you can select and download tools. Each tool includes:
- Input/Output schemas
- Usage examples
- Dependencies
- Installation instructions

### 2. Tool Structure

Each tool follows a standard structure:

```
tool_name/
│   .coveragerc
│   pyproject.toml
│   README.md
│   requirements.txt
│   uv.lock
│
├── tool/
│   │   tool_name.py
│   │   some_util_file.py
│
└── tests/
    │   test_tool_name.py
    │   test_some_util_file.py
```

### 3. Using a Tool

Here's an example of using a downloaded tool:

```python
from calculator.tool.calculator import (
    CalculatorTool,
    CalculatorInputSchema,
    CalculatorToolConfig
)

# Initialize the tool
calculator = CalculatorTool(
    config=CalculatorToolConfig()
)

# Use the tool
result = calculator.run(
    CalculatorInputSchema(
        expression="2 + 2"
    )
)
print(f"Result: {result.value}")  # Result: 4
```

## Creating Custom Tools

You can create your own tools by following these guidelines:

### 1. Basic Structure

```python
from atomic_agents import BaseTool, BaseToolConfig, BaseIOSchema

################
# Input Schema #
################

class MyToolInputSchema(BaseIOSchema):
    """Define what your tool accepts as input"""
    value: str = Field(..., description="Input value to process")

#####################
# Output Schema(s)  #
#####################

class MyToolOutputSchema(BaseIOSchema):
    """Define what your tool returns"""
    result: str = Field(..., description="Processed result")

#################
# Configuration #
#################

class MyToolConfig(BaseToolConfig):
    """Tool configuration options"""
    api_key: str = Field(
        default=os.getenv("MY_TOOL_API_KEY"),
        description="API key for the service"
    )

#####################
# Main Tool & Logic #
#####################

class MyTool(BaseTool[MyToolInputSchema, MyToolOutputSchema]):
    """Main tool implementation"""
    input_schema = MyToolInputSchema
    output_schema = MyToolOutputSchema

    def __init__(self, config: MyToolConfig = MyToolConfig()):
        super().__init__(config)
        self.api_key = config.api_key

    def run(self, params: MyToolInputSchema) -> MyToolOutputSchema:
        # Implement your tool's logic here
        result = self.process_input(params.value)
        return MyToolOutputSchema(result=result)
```

### 2. Best Practices

- **Single Responsibility**: Each tool should do one thing well
- **Clear Interfaces**: Use explicit input/output schemas
- **Error Handling**: Validate inputs and handle errors gracefully
- **Documentation**: Include clear usage examples and requirements
- **Tests**: Write comprehensive tests for your tool
- **Dependencies**: Manually create `requirements.txt` with only runtime dependencies

### 3. Tool Requirements

- Must inherit from appropriate base classes:
  - Input/Output schemas from `BaseIOSchema`
  - Configuration from `BaseToolConfig`
  - Tool class from `BaseTool`
- Must include proper documentation
- Must include tests
- Must follow the standard directory structure

## Next Steps

1. Browse available tools in the [Atomic Forge repository](https://github.com/BrainBlend-AI/atomic-agents/tree/main/atomic-forge)
2. Try downloading and using different tools via the CLI
3. Consider creating your own tools following the guidelines
4. Share your tools with the community through pull requests
