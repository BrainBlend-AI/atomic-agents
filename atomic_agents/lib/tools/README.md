# Creating New Tools

This guide will help you create new tools based on the structure and patterns observed in `calculator_tool.py` and `searx.py`.

## Step-by-Step Guide

### 1. Import Necessary Modules

Start by importing the necessary modules. Typically, you will need `os`, `pydantic`, and any other modules specific to your tool's functionality.

```python
import os
from pydantic import BaseModel, Field
# Add other necessary imports here
```

### 2. Define Input Schema

Create a class for the input schema using `pydantic.BaseModel`. Define the fields and their descriptions. Also, include a nested `Config` class with `title`, `description`, and `json_schema_extra`.

```python
class YourToolInputSchema(BaseModel):
    # Define your input fields here
    example_field: str = Field(..., description="Description of the example field.")

    class Config:
        title = "YourTool"
        description = "Tool for performing specific tasks."
        json_schema_extra = {
            "title": title,
            "description": description
        }
```

### 3. Define Output Schema

Create a class for the output schema using `pydantic.BaseModel`. Define the fields and their descriptions.

```python
class YourToolOutputSchema(BaseModel):
    # Define your output fields here
    result: str = Field(..., description="Result of the operation.")
```

### 4. Implement the Tool Logic

Create a class for your tool. Define `input_schema` and `output_schema` attributes. Implement the `run` method to process the input and produce the output.

```python
class YourTool:
    input_schema = YourToolInputSchema
    output_schema = YourToolOutputSchema

    def run(self, params: YourToolInputSchema) -> YourToolOutputSchema:
        try:
            # Implement your tool logic here
            result = "Your result here"
            return YourToolOutputSchema(result=result)
        except Exception as e:
            raise ValueError(f"Error processing input: {e}")
```

### 5. Example Usage

Include an example usage section to demonstrate how to initialize and use your tool.

```python
if __name__ == "__main__":
    # Initialize your tool
    your_tool = YourTool()

    # Create input parameters
    input_params = YourToolInputSchema(
        example_field="Example input"
    )

    # Run the tool and get the output
    output = your_tool.run(input_params)

    # Print the result
    print(output)
```

## Example

Here is a complete example of a simple tool that echoes the input string.

```python
import os
from pydantic import BaseModel, Field

class EchoToolInputSchema(BaseModel):
    message: str = Field(..., description="Message to echo.")

    class Config:
        title = "EchoTool"
        description = "Tool for echoing messages."
        json_schema_extra = {
            "title": title,
            "description": description
        }

class EchoToolOutputSchema(BaseModel):
    echoed_message: str = Field(..., description="Echoed message.")

class EchoTool:
    input_schema = EchoToolInputSchema
    output_schema = EchoToolOutputSchema

    def run(self, params: EchoToolInputSchema) -> EchoToolOutputSchema:
        try:
            echoed_message = params.message
            return EchoToolOutputSchema(echoed_message=echoed_message)
        except Exception as e:
            raise ValueError(f"Error echoing message: {e}")

if __name__ == "__main__":
    echo_tool = EchoTool()
    input_params = EchoToolInputSchema(message="Hello, World!")
    output = echo_tool.run(input_params)
    print(output)
```

By following this guide, you can create new tools with a consistent structure and easily integrate them into your projects.