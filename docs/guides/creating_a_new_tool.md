# Tools
## Creating a New Tool

This guide will walk you through the steps to create a new tool in the `atomic_agents` framework. We will cover the necessary components and provide an example to illustrate the process.

### Components of a Tool

A tool in the `atomic_agents` framework consists of the following components:

1. **Input Schema**: Defines the input parameters for the tool.
2. **Output Schema**: Defines the output structure of the tool.
3. **Tool Logic**: Implements the core functionality of the tool.
4. **Example Usage**: Demonstrates how to use the tool.

### Step-by-Step Guide

#### 1. Define the Input Schema

The input schema is a Pydantic `BaseModel` that specifies the input parameters for the tool. It can include simple fields, complex nested data structures, and even child schemas.
An input schema should include a `Config` class with `title`, `description`, and `json_schema_extra` attributes. This is not just informational or aesthetic; it also helps generate the OpenAPI documentation for the tool, which is consumed by the LLM in order to generate the output.
Here is an example:

```python
from pydantic import BaseModel, Field

class ChildSchema(BaseModel):
    child_param: int = Field(..., description="A parameter in the child schema.")

class MyToolInputSchema(BaseModel):
    parameter: str = Field(..., description="Description of the parameter.")
    nested: ChildSchema = Field(..., description="A nested schema example.")
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

The output schema is a Pydantic `BaseModel` that specifies the structure of the tool's output. It can also include complex nested data structures and multiple properties just like the input schema. Here is an example:

```python
class MyToolOutputSchema(BaseModel):
    result: str = Field(..., description="Result of the tool's operation.")
    details: dict = Field(..., description="Additional details about the result.")
```

#### 3. Implement the Tool Logic

Create a class that inherits from `BaseTool` and implements the core functionality of the tool. This class should define the `input_schema` and `output_schema` attributes and implement the `run` method.

```python
from typing import Optional
from atomic_agents.lib.tools.base import BaseTool

class MyTool(BaseTool):
    input_schema = MyToolInputSchema
    output_schema = MyToolOutputSchema
    
    def __init__(self, tool_description_override: Optional[str] = None):
        super().__init__(tool_description_override)
    
    def run(self, params: MyToolInputSchema) -> MyToolOutputSchema:
        # Implement the core logic here
        result = f"Processed {params.parameter} with child param {params.nested.child_param}"
        details = {"list_param_length": len(params.list_param)}
        return MyToolOutputSchema(result=result, details=details)
```

#### 4. Example Usage

Provide an example of how to use the tool. This typically involves initializing the tool and running it with sample input. If you don't plan to merge this tool into the atomic_agents repository, you can exclude this part if you wish.

```python
if __name__ == "__main__":
    # Example usage of MyTool
    input_data = MyToolInputSchema(
        parameter="example input",
        nested=ChildSchema(child_param=42),
        list_param=["item1", "item2"]
    )
    tool = MyTool()
    output = tool.run(input_data)
    print(output)
```

### Full Example

Here is a complete example of a new tool called `MyTool`:

```python
# my_tool.py

from pydantic import BaseModel, Field
from typing import Optional
from atomic_agents.lib.tools.base import BaseTool

# Child Schema
class ChildSchema(BaseModel):
    child_param: int = Field(..., description="A parameter in the child schema.")

# Input Schema
class MyToolInputSchema(BaseModel):
    parameter: str = Field(..., description="Description of the parameter.")
    nested: ChildSchema = Field(..., description="A nested schema example.")
    list_param: list[str] = Field(..., description="A list of strings.")

    class Config:
        title = "MyTool"
        description = "Description of what MyTool does."
        json_schema_extra = {
            "title": title,
            "description": description
        }

# Output Schema
class MyToolOutputSchema(BaseModel):
    result: str = Field(..., description="Result of the tool's operation.")
    details: dict = Field(..., description="Additional details about the result.")

# Tool Logic
class MyTool(BaseTool):
    input_schema = MyToolInputSchema
    output_schema = MyToolOutputSchema
    
    def __init__(self, tool_description_override: Optional[str] = None):
        super().__init__(tool_description_override)
    
    def run(self, params: MyToolInputSchema) -> MyToolOutputSchema:
        # Implement the core logic here
        result = f"Processed {params.parameter} with child param {params.nested.child_param}"
        details = {"list_param_length": len(params.list_param)}
        return MyToolOutputSchema(result=result, details=details)

# Example Usage
if __name__ == "__main__":
    # Example usage of MyTool
    input_data = MyToolInputSchema(
        parameter="example input",
        nested=ChildSchema(child_param=42),
        list_param=["item1", "item2"]
    )
    tool = MyTool()
    output = tool.run(input_data)
    print(output)
```

### Conclusion

By following these steps, you can create a new tool in the `atomic_agents` framework. Define the input and output schemas, implement the tool logic, and provide an example usage to demonstrate how the tool works. Remember that the input and output schemas can be as simple or as complex as needed, including nested data structures and multiple properties.