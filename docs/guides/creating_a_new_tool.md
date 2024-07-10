# Tools
## Creating a New Tool

This guide will walk you through the steps to create a new tool in the `atomic_agents` framework. We will cover the necessary components and provide an example to illustrate the process.

### Components of a Tool

A tool in the `atomic_agents` framework consists of the following components:

1. **Input Schema**: Defines the input parameters for the tool.
2. **Output Schema**: Defines the output structure of the tool.
3. **Tool Logic**: Implements the core functionality of the tool.
4. **Configuration**: Defines the configuration parameters for the tool.
5. **Example Usage**: Demonstrates how to use the tool.

### Step-by-Step Guide

#### 1. Define the Input Schema

The input schema is a Pydantic `BaseModel` that specifies the input parameters for the tool. It should inherit from `BaseAgentIO` and include a `Config` class with `title`, `description`, and `json_schema_extra` attributes. Here's an example:

```python
from pydantic import Field
from atomic_agents.agents.base_agent import BaseAgentIO

class MyToolInputSchema(BaseAgentIO):
    parameter: str = Field(..., description="Description of the parameter.")
    list_param: list[str] = Field(..., description="A list of strings.")

    class Config:
        title = "MyTool"
        description = "Description of what MyTool does."
        json_schema_extra = {
            "title": title,
            "description": description
        }
```

#### 2. Define the Output Schema

The output schema is also a Pydantic `BaseModel` that inherits from `BaseAgentIO`. It specifies the structure of the tool's output. Here's an example:

```python
class MyToolOutputSchema(BaseAgentIO):
    result: str = Field(..., description="Result of the tool's operation.")
    details: dict = Field(..., description="Additional details about the result.")
```

#### 3. Define the Configuration

The configuration is a Pydantic `BaseModel` that specifies the configuration parameters for the tool. It should extend from `BaseToolConfig`. Here's an example:

```python
from atomic_agents.lib.tools.base import BaseToolConfig

class MyToolConfig(BaseToolConfig):
    api_key: str = Field(..., description="API key for accessing external services.")
```

#### 4. Implement the Tool Logic

Create a class that inherits from `BaseTool` and implements the core functionality of the tool. This class should define the `input_schema`, `output_schema`, and implement the `run` method.

```python
from atomic_agents.lib.tools.base import BaseTool

class MyTool(BaseTool):
    input_schema = MyToolInputSchema
    output_schema = MyToolOutputSchema
    
    def __init__(self, config: MyToolConfig = MyToolConfig()):
        super().__init__(config)
        self.api_key = config.api_key

    def run(self, params: MyToolInputSchema) -> MyToolOutputSchema:
        # Implement the core logic here
        result = f"Processed {params.parameter}"
        details = {"list_param_length": len(params.list_param)}
        return MyToolOutputSchema(result=result, details=details)
```

#### 5. Example Usage

Provide an example of how to use the tool. This typically involves initializing the tool and running it with sample input.

```python
if __name__ == "__main__":
    from rich.console import Console

    rich_console = Console()
    
    input_data = MyToolInputSchema(
        parameter="example input",
        list_param=["item1", "item2"]
    )
    config = MyToolConfig(api_key="your_api_key_here")
    tool = MyTool(config=config)
    output = tool.run(input_data)
    rich_console.print(output)
```

### Full Example

Here is a complete example of a new tool called `MyTool`:

```python
# my_tool.py

from pydantic import Field
from atomic_agents.agents.base_agent import BaseAgentIO
from atomic_agents.lib.tools.base import BaseTool, BaseToolConfig
from rich.console import Console

# Input Schema
class MyToolInputSchema(BaseAgentIO):
    parameter: str = Field(..., description="Description of the parameter.")
    list_param: list[str] = Field(..., description="A list of strings.")

    class Config:
        title = "MyTool"
        description = "Description of what MyTool does."
        json_schema_extra = {
            "title": title,
            "description": description
        }

# Output Schema
class MyToolOutputSchema(BaseAgentIO):
    result: str = Field(..., description="Result of the tool's operation.")
    details: dict = Field(..., description="Additional details about the result.")

# Configuration
class MyToolConfig(BaseToolConfig):
    api_key: str = Field(..., description="API key for accessing external services.")

# Tool Logic
class MyTool(BaseTool):
    input_schema = MyToolInputSchema
    output_schema = MyToolOutputSchema
    
    def __init__(self, config: MyToolConfig = MyToolConfig()):
        super().__init__(config)
        self.api_key = config.api_key

    def run(self, params: MyToolInputSchema) -> MyToolOutputSchema:
        # Implement the core logic here
        result = f"Processed {params.parameter}"
        details = {"list_param_length": len(params.list_param)}
        return MyToolOutputSchema(result=result, details=details)

# Example Usage
if __name__ == "__main__":
    rich_console = Console()
    
    input_data = MyToolInputSchema(
        parameter="example input",
        list_param=["item1", "item2"]
    )
    config = MyToolConfig(api_key="your_api_key_here")
    tool = MyTool(config=config)
    output = tool.run(input_data)
    rich_console.print(output)
```

### Conclusion

By following these steps, you can create a new tool in the `atomic_agents` framework. Define the input and output schemas, implement the tool logic, and provide an example usage to demonstrate how the tool works. Remember to inherit from the appropriate base classes (`BaseAgentIO`, `BaseToolConfig`, and `BaseTool`) and use the `rich` library for console output in your example usage.
