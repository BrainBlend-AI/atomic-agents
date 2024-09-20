# Anatomy of a Tool in Atomic Agents

## Introduction

The **Atomic Agents** framework enables developers to create modular, extensible, and efficient AI tools. This guide outlines the core anatomy of a tool within the Atomic Agents ecosystem, providing a structured approach to building new tools that seamlessly integrate into the framework.

## Components of a Tool

Each tool in Atomic Agents is constructed using a standardized architecture to ensure consistency and ease of integration. The primary components include:

1. **Input Schema**
2. **Output Schema**
3. **Tool Logic**
4. **Configuration**
5. **Example Usage**

### 1. Input Schema

The Input Schema defines the structure and validation rules for the data the tool expects. Utilizing Pydantic's `BaseModel`, it ensures that all inputs meet the required criteria before processing.

**Example: `CalculatorToolInputSchema`**

```python:atomic_tools/calculator/tool/calculator.py
class CalculatorToolInputSchema(BaseIOSchema):
    """
    Tool for performing calculations. Supports basic arithmetic operations
    like addition, subtraction, multiplication, and division, as well as more
    complex operations like exponentiation and trigonometric functions.
    Use this tool to evaluate mathematical expressions.
    """

    expression: str = Field(
        ..., description="Mathematical expression to evaluate. For example, '2 + 2'."
    )
```

### 2. Output Schema

The Output Schema defines the structure and validation rules for the data the tool returns after execution. It ensures that the output adheres to a consistent format, facilitating seamless integration with other components.

**Example: `CalculatorToolOutputSchema`**

```python:atomic_tools/calculator/tool/calculator.py
class CalculatorToolOutputSchema(BaseIOSchema):
    """This schema defines the output of the CalculatorTool."""

    result: str = Field(..., description="Result of the calculation.")
```

### 3. Tool Logic

The Tool Logic encapsulates the core functionality of the tool, detailing how inputs are processed to produce outputs. It inherits from a base tool class and implements the `run` method, which orchestrates the tool's operations.

**Example: `CalculatorTool`**

```python:atomic_tools/calculator/tool/calculator.py
class CalculatorTool(BaseTool):
    """
    Tool for performing calculations based on the provided mathematical expression.

    Attributes:
        input_schema (CalculatorToolInputSchema): The schema for the input data.
        output_schema (CalculatorToolOutputSchema): The schema for the output data.
    """

    input_schema = CalculatorToolInputSchema
    output_schema = CalculatorToolOutputSchema

    def __init__(self, config: CalculatorToolConfig = CalculatorToolConfig()):
        """
        Initializes the CalculatorTool.

        Args:
            config (CalculatorToolConfig): Configuration for the tool.
        """
        super().__init__(config)

    def run(self, params: CalculatorToolInputSchema) -> CalculatorToolOutputSchema:
        """
        Executes the CalculatorTool with the given parameters.

        Args:
            params (CalculatorToolInputSchema): The input parameters for the tool.

        Returns:
            CalculatorToolOutputSchema: The result of the calculation.
        """
        # Convert the expression string to a symbolic expression
        parsed_expr = sympify(params.expression)

        # Evaluate the expression numerically
        result = parsed_expr.evalf()
        return CalculatorToolOutputSchema(result=str(result))
```

### 4. Configuration

Configuration handles the settings required by the tool, such as API keys or environment variables. It ensures that sensitive information is managed securely and can be easily modified without altering the tool's core logic.

**Example: `YouTubeTranscriptToolConfig`**

```python:atomic_tools/youtube_transcript_scraper/tool/youtube_transcript_scraper.py
class YouTubeTranscriptToolConfig(BaseToolConfig):
    api_key: str = Field(
        description="YouTube API key for fetching video metadata.",
        default=os.getenv("YOUTUBE_API_KEY"),
    )
```

### 5. Example Usage

Example Usage demonstrates how to instantiate and utilize the tool within an application. It provides a practical reference for developers to integrate the tool into their workflows effectively.

**Example Usage: `CalculatorTool`**

```python:atomic_tools/calculator/tool/calculator.py
if __name__ == "__main__":
    calculator = CalculatorTool()
    result = calculator.run(
        CalculatorToolInputSchema(expression="sin(pi/2) + cos(pi/4)")
    )
    print(result)  # Expected output: {"result":"1.70710678118655"}
```

## Creating a New Tool

To create a new tool within the Atomic Agents framework, follow these steps:

1. **Define the Input Schema:**
   Specify the input parameters the tool will accept using a Pydantic `BaseModel`.

   **Example:**
   ```python:your_tool/tool/your_tool.py
   class YourToolInputSchema(BaseIOSchema):
       """
       Description of your tool's input parameters.
       """
       param1: str = Field(..., description="Description of param1.")
       param2: int = Field(..., description="Description of param2.")
   ```

2. **Define the Output Schema:**
   Specify the structure of the data the tool will return after execution.

   **Example:**
   ```python:your_tool/tool/your_tool.py
   class YourToolOutputSchema(BaseIOSchema):
       """
       Description of the tool's output.
       """
       result: str = Field(..., description="Description of the result.")
   ```

3. **Implement the Tool Logic:**
   Create a class that inherits from `BaseTool`, set the `input_schema` and `output_schema`, and implement the `run` method with the tool's functionality.

   **Example:**
   ```python:your_tool/tool/your_tool.py
   class YourTool(BaseTool):
       """
       Tool for [brief description of what your tool does].

       Attributes:
           input_schema (YourToolInputSchema): The schema for the input data.
           output_schema (YourToolOutputSchema): The schema for the output data.
       """

       input_schema = YourToolInputSchema
       output_schema = YourToolOutputSchema

       def __init__(self, config: YourToolConfig = YourToolConfig()):
           """
           Initializes the YourTool.

           Args:
               config (YourToolConfig): Configuration for the tool.
           """
           super().__init__(config)

       def run(self, params: YourToolInputSchema) -> YourToolOutputSchema:
           """
           Executes the YourTool with the given parameters.

           Args:
               params (YourToolInputSchema): The input parameters for the tool.

           Returns:
               YourToolOutputSchema: The result of the tool's execution.
           """
           # Implement your tool's logic here
           result = "your_result_based_on_params"
           return YourToolOutputSchema(result=result)
   ```

4. **Configure the Tool:**
   Create a configuration class inheriting from `BaseToolConfig` to manage any necessary settings or environment variables.

   **Example:**
   ```python:your_tool/tool/your_tool.py
   class YourToolConfig(BaseToolConfig):
       """
       Configuration for YourTool.

       Attributes:
           setting1 (str): Description of setting1.
           setting2 (int): Description of setting2.
       """
       setting1: str = Field(..., description="Description of setting1.")
       setting2: int = Field(..., description="Description of setting2.")
   ```

5. **Provide Example Usage:**
   Add examples demonstrating how to use the tool, aiding developers in integration.

   **Example Usage:**
   ```python:your_tool/tool/your_tool.py
   if __name__ == "__main__":
       tool = YourTool()
       input_data = YourToolInputSchema(param1="value1", param2=42)
       output = tool.run(input_data)
       print(output)  # Expected output: {"result":"expected_result"}
   ```

6. **Write Tests:**
   Develop test cases to validate the tool's functionality, ensuring it behaves as expected.

   **Example Test:**
   ```python:your_tool/tests/test_your_tool.py
   import pytest
   from your_tool.tool.your_tool import YourTool, YourToolInputSchema, YourToolOutputSchema, YourToolConfig

   def test_your_tool():
       config = YourToolConfig(setting1="value1", setting2=2)
       tool = YourTool(config=config)
       input_data = YourToolInputSchema(param1="test", param2=10)
       result = tool.run(input_data)
       assert isinstance(result, YourToolOutputSchema)
       assert result.result == "expected_result_based_on_input"
   ```

## Best Practices

- **Modularity:** Design tools to perform single, well-defined tasks to enhance reusability and maintainability.
- **Validation:** Utilize Pydantic schemas for rigorous input and output validation, ensuring data integrity.
- **Error Handling:** Implement comprehensive error checks to manage unexpected scenarios gracefully.
- **Configuration Management:** Securely handle sensitive information like API keys using environment variables and configuration classes.
- **Documentation:** Provide clear docstrings and usage examples to aid developers in understanding and utilizing the tools effectively.
- **Testing:** Develop thorough test cases to validate the tool's functionality and reliability across different scenarios.

## Conclusion

Mastering the anatomy of a tool within the Atomic Agents framework enables the creation of robust and efficient AI-driven applications. By adhering to the structured approach outlined in this guide, developers can ensure consistency, reliability, and scalability in their tool development endeavors.

For more detailed information and advanced configurations, refer to the [Atomic Agents Documentation](https://github.com/BrainBlend-AI/atomic-agents).
