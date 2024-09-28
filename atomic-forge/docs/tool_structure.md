# Creating Your Own Atomic Tool: A Comprehensive Guide

## Introduction

Welcome to this (hopefully) comprehensive (enough) guide on creating your own **Atomic Tool** within the **Atomic Agents** framework. This guide is designed to be a step-by-step tutorial, walking you through the entire process of building an Atomic Tool—from understanding the fundamental concepts to implementing and testing your tool.

## The Principles

An **Atomic Tool** is a self-contained, modular component within the Atomic Agents framework. It encapsulates a specific piece of functionality, for example a calculator, a youtube transcript scraper, or a twitter search tool, allowing for easy integration, maintenance, and extension. Each tool is designed to perform a single task and can be combined with other tools to build more complex applications.

**Key Characteristics of an Atomic Tool:**

- **Single Responsibility:** Focuses on one specific task.
- **Modular and Reusable:** Can be easily integrated into different agents or applications.
- **Self-Contained:** Includes all necessary components to function independently.
- **Clear Interfaces:** Defines explicit input and output schemas for consistent data handling.
- **Configurable:** Allows customization through configuration settings.
- **Executable Independently:** Can run on its own or as part of an Atomic Agent.

## Principles of Atomic Tool Design

### Modularity

Each tool should be an independent module that can function on its own. Modularity ensures that tools can be developed, tested, and debugged in isolation, leading to more reliable and maintainable code.

### Reusability

Design tools with reusability in mind. Avoid hardcoding values or making assumptions that limit where and how the tool can be used.

### Single Responsibility Principle

Adhere to the Single Responsibility Principle by ensuring that each tool does one thing and does it well. This makes your tools easier to understand, test, and maintain.

### Clear Interfaces

Define explicit input and output schemas using Pydantic models. This ensures consistent data handling and makes your tools predictable and reliable.

### Configurability

Provide configuration options to allow users to customize the tool's behavior without modifying the code. Use default values where appropriate to make tools easy to use out of the box.

## Anatomy of an Atomic Tool

An Atomic Tool in the Atomic Agents framework follows a highly standardized structure. This consistency is crucial for maintainability, interoperability, and ease of understanding.

**The structure of an Atomic Tool includes the following sections, in this specific order:**

1. **Input Schema**
2. **Output Schema(s)**
3. **Configuration**
4. **Main Tool & Logic**
5. **Example Usage**

The input and output schemas must always extend from `BaseIOSchema` and the main tool class must always extend from `BaseTool`.

**Note:** Each section should be clearly delineated with a comment block that includes the section's name. For example:

```python
################
# Input Schema #
################
```

Let's explore each of these sections in detail.

### 1. Input Schema

The **Input Schema** defines the structure and validation rules for the data your tool accepts. It uses Pydantic models to enforce data types, provide default values, and include descriptions.

**Guidelines:**

- Use `BaseIOSchema` as the base class.
- Define all input fields with appropriate types and descriptions.
- Use `Field(..., description="...")` to make a field required and to provide a description.
- Include a docstring that briefly explains the purpose of the input schema.

**Example:**

```python
################
# Input Schema #
################

class MyToolInputSchema(BaseIOSchema):
    """
    Captures input data required for MyTool.
    """
    input_field1: str = Field(..., description="Description of input_field1.")
    input_field2: int = Field(42, description="Description of input_field2 with a default value.")
```

### 2. Output Schema(s)

The **Output Schema(s)** define the structure of the data your tool outputs. You can have multiple output schemas if your tool produces different types of outputs.

**Guidelines:**

- Use `BaseIOSchema` as the base class.
- Define all output fields with appropriate types and descriptions.
- Include a docstring that briefly explains the purpose of the output schema.

**Example:**

```python
#################
# Output Schema #
#################

class MyToolOutputSchema(BaseIOSchema):
    """
    Contains the results produced by MyTool.
    """
    output_field1: str = Field(..., description="Description of output_field1.")
```

### 3. Configuration

The **Configuration** section allows you to define settings that can customize the tool's behavior. This is where you include API keys, endpoints, or any other parameters that might change between environments or use cases.

**Guidelines:**

- Inherit from `BaseToolConfig`.
- Define configuration parameters with default values and descriptions.
- Use environment variables where appropriate to avoid hardcoding sensitive information.
- Include a docstring that explains the purpose of the configuration class.

**Example:**

```python
#################
# Configuration #
#################

class MyToolConfig(BaseToolConfig):
    """
    Configuration settings for MyTool.
    """
    api_endpoint: str = Field(
        default="https://api.example.com/v1",
        description="API endpoint for MyTool."
    )
    api_key: str = Field(
        default=os.getenv("MY_TOOL_API_KEY"),
        description="API key for authenticating with the service."
    )
```

### 4. Main Tool & Logic

This is the core of your tool, where you implement the main functionality.

**Guidelines:**

- Inherit from `BaseTool`.
- Set `input_schema` and `output_schema` as class variables.
- Implement the `run` method, which takes an instance of the input schema and returns an instance of the output schema.
- Include a docstring that explains what the tool does.
- Use helper methods to break down complex logic.
- Handle exceptions gracefully, providing meaningful error messages.

**Example:**

```python
#####################
# Main Tool & Logic #
#####################

class MyTool(BaseTool):
    """
    Performs the main functionality of MyTool.
    """

    input_schema = MyToolInputSchema
    output_schema = MyToolOutputSchema

    def __init__(self, config: MyToolConfig = MyToolConfig()):
        """
        Initializes MyTool with the provided configuration.
        """
        super().__init__(config)
        self.api_endpoint = config.api_endpoint
        self.api_key = config.api_key

    def run(self, params: MyToolInputSchema) -> MyToolOutputSchema:
        """
        Executes the tool's main logic.
        """
        # Implement the logic here
        result = self.perform_action(params.input_field1, params.input_field2)
        return MyToolOutputSchema(output_field1=result)

    def perform_action(self, field1: str, field2: int) -> str:
        """
        Helper method to perform a specific action.
        """
        # Example logic
        return f"Processed {field1} with value {field2}"
```

### 5. Example Usage

The **Example Usage** section demonstrates how to instantiate and run your tool. This is invaluable for testing and serves as documentation for users.

**Guidelines:**

- Include a `__main__` guard to prevent code from running on import.
- Use `rich.console` for formatted output.
- Provide sample input data.
- Print or log the output in a readable format.

**Example:**

```python
#################
# Example Usage #
#################

if __name__ == "__main__":
    from rich.console import Console

    console = Console()
    tool = MyTool()

    input_data = MyToolInputSchema(
        input_field1="Sample Input",
        input_field2=123
    )

    output = tool.run(input_data)
    console.print(output)
```

## Step-by-Step Guide to Creating an Atomic Tool

Now that we've covered the structure, let's go through the steps to create your own Atomic Tool.

### Step 1: Define the Purpose of Your Tool

Before writing any code, clearly define what your tool will do.

- **Example:** "I want to create a tool that fetches the current weather for a given city."

### Step 2: Design the Input Schema

Identify what inputs your tool requires.

- **Example Input Fields:**
  - `city_name`: Name of the city.
  - `units`: Units of measurement (e.g., metric or imperial).

Implement the input schema:

```python
################
# Input Schema #
################

class WeatherToolInputSchema(BaseIOSchema):
    """
    Input data required to fetch the weather.
    """
    city_name: str = Field(..., description="Name of the city to fetch the weather for.")
    units: str = Field('metric', description="Units of measurement (metric or imperial).")
```

### Step 3: Design the Output Schema

Determine what outputs your tool will produce.

- **Example Output Fields:**
  - `temperature`: Current temperature.
  - `description`: Weather description (e.g., sunny, cloudy).

Implement the output schema:

```python
####################
# Output Schema(s) #
####################

class WeatherToolOutputSchema(BaseIOSchema):
    """
    Weather data for the specified city.
    """
    temperature: float = Field(..., description="Current temperature in the specified units.")
    description: str = Field(..., description="Weather description.")
```

### Step 4: Set Up Configuration

Identify any configuration parameters, such as API keys or endpoints.

Implement the configuration class:

```python
#################
# Configuration #
#################

class WeatherToolConfig(BaseToolConfig):
    """
    Configuration for the WeatherTool.
    """
    api_key: str = Field(
        default=os.getenv("WEATHER_API_KEY"),
        description="API key for the weather service."
    )
    api_endpoint: str = Field(
        default="https://api.openweathermap.org/data/2.5/weather",
        description="API endpoint for fetching weather data."
    )
```

### Step 5: Implement the Main Tool & Logic

Create the tool class and implement the logic.

```python
#####################
# Main Tool & Logic #
#####################

class WeatherTool(BaseTool):
    """
    Fetches the current weather for a specified city.
    """

    input_schema = WeatherToolInputSchema
    output_schema = WeatherToolOutputSchema

    def __init__(self, config: WeatherToolConfig = WeatherToolConfig()):
        super().__init__(config)
        self.api_key = config.api_key
        self.api_endpoint = config.api_endpoint

    def run(self, params: WeatherToolInputSchema) -> WeatherToolOutputSchema:
        response = self.fetch_weather(params.city_name, params.units)
        temperature = response['main']['temp']
        description = response['weather'][0]['description']
        return WeatherToolOutputSchema(
            temperature=temperature,
            description=description
        )

    def fetch_weather(self, city_name: str, units: str) -> dict:
        import requests
        params = {
            'q': city_name,
            'units': units,
            'appid': self.api_key
        }
        response = requests.get(self.api_endpoint, params=params)
        if response.status_code != 200:
            raise Exception(f"Error fetching weather data: {response.text}")
        return response.json()
```

**Notes:**

- **Error Handling:** We check the response status code and raise an exception if the request fails.
- **Helper Methods:** `fetch_weather` is a helper method that encapsulates the API call.

### Step 6: Test Your Tool

Write an example usage to test the tool.

```python
#################
# Example Usage #
#################

if __name__ == "__main__":
    from rich.console import Console

    console = Console()
    tool = WeatherTool()

    input_data = WeatherToolInputSchema(
        city_name="New York",
        units="metric"
    )

    try:
        output = tool.run(input_data)
        console.print(output)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
```

**Testing Tips:**

- Test with valid and invalid inputs.
- Check how the tool handles exceptions.
- Ensure the output matches the expected schema.

## Best Practices and Guidelines

### Do's

- **Follow the Standard Structure:** Adhere to the prescribed order and format for consistency.
- **Use Clear and Descriptive Names:** Make your code self-explanatory.
- **Document Your Code:** Include docstrings and comments to explain the purpose and functionality.
- **Validate Inputs Thoroughly:** Use Pydantic's features to enforce data integrity.
- **Handle Errors Gracefully:** Provide informative error messages and handle exceptions where appropriate.
- **Keep Functions Small and Focused:** Break down complex logic into helper methods.
- **Test Extensively:** Use the example usage section to test various scenarios.

### Don'ts

- **Don't Hardcode Values:** Use configuration parameters or environment variables instead.
- **Avoid Global Variables:** Keep the state within your tool's scope.
- **Don't Overcomplicate:** Stick to the tool's single responsibility; avoid adding unrelated features.
- **Don't Ignore Security:** Be cautious with sensitive information like API keys; use environment variables.
- **Don't Neglect Performance:** Optimize your code, especially when dealing with large datasets or external API calls.
- **Don't Skip Input Validation:** Never assume inputs are valid; always validate.

## Example: Pizza Ordering Tool

To illustrate the concepts, let's revisit the **Pizza Ordering Tool** example, explaining each section in detail.

### Input Schema

We need to capture customer details and order specifics.

```python
################
# Input Schema #
################

class PizzaOrderInputSchema(BaseIOSchema):
    """
    Captures customer details and order specifics for placing a pizza order.
    """
    customer_name: str = Field(..., description="Name of the customer placing the order.")
    pizza_type: str = Field(..., description="Type of pizza to order (e.g., Margherita, Pepperoni).")
    size: str = Field(..., description="Size of the pizza (e.g., Small, Medium, Large).")
    quantity: int = Field(..., description="Number of pizzas to order.")
```

**Explanation:**

- All fields are required, indicated by `...`.
- Each field has a descriptive message.
- The schema is clear and self-explanatory.

### Output Schemas

We have two outputs: order confirmation and payment details.

```python
####################
# Output Schemas #
####################

class OrderConfirmationSchema(BaseIOSchema):
    """
    Confirmation details of the placed order.
    """
    order_id: str = Field(..., description="Unique identifier for the order.")
    estimated_delivery_time: str = Field(..., description="Estimated time for order delivery.")

class PaymentDetailsSchema(BaseIOSchema):
    """
    Payment information for the order.
    """
    amount: float = Field(..., description="Total amount to be paid.")
    payment_status: str = Field(..., description="Status of the payment (e.g., Paid, Pending).")
```

**Explanation:**

- Separate schemas for different types of outputs.
- Clear and descriptive fields.

### Configuration

Defines API endpoints and supported pizzas.

```python
#################
# Configuration #
#################

class PizzaOrderingToolConfig(BaseToolConfig):
    """
    Configuration for the PizzaOrderingTool.
    """
    api_endpoint: str = Field(
        default="https://api.pizzaorders.com/v1/orders",
        description="API endpoint for processing pizza orders."
    )
    supported_pizzas: List[str] = Field(
        default=["Margherita", "Pepperoni", "Veggie", "Hawaiian"],
        description="List of supported pizza types."
    )
```

**Explanation:**

- Allows the tool to be customized without changing the code.
- Uses defaults that can be overridden if necessary.

### Main Tool & Logic

Implements the tool's functionality.

```python
#####################
# Main Tool & Logic #
#####################

class PizzaOrderingTool(BaseTool):
    """
    Tool for placing pizza orders through the Pizza Orders API.
    """

    input_schema = PizzaOrderInputSchema
    output_schemas = {
        "confirmation": OrderConfirmationSchema,
        "payment": PaymentDetailsSchema
    }

    def __init__(self, config: PizzaOrderingToolConfig = PizzaOrderingToolConfig()):
        super().__init__(config)
        self.api_endpoint = config.api_endpoint
        self.supported_pizzas = config.supported_pizzas

    def run(self, params: PizzaOrderInputSchema) -> Dict[str, BaseIOSchema]:
        # Validate pizza type
        if params.pizza_type not in self.supported_pizzas:
            raise ValueError(f"Pizza type '{params.pizza_type}' is not supported.")

        # Simulate placing the order
        order_id = self.place_order(params)
        estimated_time = self.get_estimated_delivery_time(order_id)
        amount = self.calculate_payment(params)
        payment_status = self.process_payment(order_id, amount)

        # Prepare outputs
        confirmation = OrderConfirmationSchema(
            order_id=order_id,
            estimated_delivery_time=estimated_time
        )
        payment = PaymentDetailsSchema(
            amount=amount,
            payment_status=payment_status
        )

        return {
            "confirmation": confirmation,
            "payment": payment
        }

    def place_order(self, params: PizzaOrderInputSchema) -> str:
        """
        Simulates placing an order and returns an order ID.
        """
        # Placeholder logic; in reality, this would involve an API call.
        return "ORD123456"

    def get_estimated_delivery_time(self, order_id: str) -> str:
        """
        Simulates retrieving the estimated delivery time.
        """
        # Placeholder logic.
        return "30 minutes"

    def calculate_payment(self, params: PizzaOrderInputSchema) -> float:
        """
        Calculates the total amount to be paid.
        """
        price_per_pizza = {
            "Margherita": 8.99,
            "Pepperoni": 9.99,
            "Veggie": 10.99,
            "Hawaiian": 9.49
        }
        return price_per_pizza[params.pizza_type] * params.quantity

    def process_payment(self, order_id: str, amount: float) -> str:
        """
        Simulates payment processing.
        """
        # Placeholder logic.
        return "Paid"
```

**Explanation:**

- **Validation:** Checks if the pizza type is supported.
- **Modularity:** Uses helper methods for each step.
- **Error Handling:** Raises exceptions for invalid inputs.
- **Output Preparation:** Constructs output schemas to return.

### Example Usage

Testing the tool.

```python
#################
# Example Usage #
#################

if __name__ == "__main__":
    from rich.console import Console

    console = Console()
    pizza_tool = PizzaOrderingTool()

    order_input = PizzaOrderInputSchema(
        customer_name="Jane Smith",
        pizza_type="Veggie",
        size="Medium",
        quantity=1
    )

    try:
        outputs = pizza_tool.run(order_input)
        console.print(outputs)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
```

**Remember:** The goal of the Atomic Agents framework is to build powerful applications by composing small, well-defined tools and agents. Your contributions help make the framework more robust and versatile.

---

By following this guide and adhering to the best practices outlined, you'll be well on your way to creating effective and reusable Atomic Tools that can be combined to build powerful AI applications. Happy coding!
