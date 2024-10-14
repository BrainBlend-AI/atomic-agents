# Creating Your Own Atomic Tool: A Comprehensive Guide

## Introduction

This guide aims to explain the anatomy of an **Atomic Tool** within the **Atomic Agents** framework and help you get started adding your own tools, either to your own project or to the repository to share with others. We'll walk through the entire process step-by-step, using a mock **Pizza Ordering Tool** as our running example.

## Prerequisites

Set up the main Atomic Agents library for development by following the instructions in the [development setup guide](/guides/dev-setup.md).

## The Principles

An **Atomic Tool** should always be self-contained and modular. This means it should encapsulate specific functionality, such as a calculator, a YouTube transcript scraper, or, in our case, a pizza ordering service. Each tool should be runnable both standalone and by an AI Agent, allowing for easy integration, maintenance, and extension.

**An Atomic Tool should always have / be:**

- **Single Responsibility:** Focuses on one specific task.
- **Modular and Reusable:** Easily integrated into different agents or applications.
- **Self-Contained:** Includes all necessary components to function independently.
- **Clear Interfaces:** Defines explicit input and output schemas for consistent data handling.
- **Configurable:** Allows customization through configuration settings.
- **Executable Independently:** Can run on its own or as part of an Atomic Agent.

## Anatomy of an Atomic Tool

### Folder Structure

Each tool should be placed in its own folder with the following structure:

```
tool_name/
│   .coveragerc
│   pyproject.toml
│   README.md
│   requirements.txt
│   poetry.lock
│
├── tool/
│   │   tool_name.py
│   │   some_util_file.py
│   │   another_util_file.py
│
└── tests/
    │   test_tool_name.py
    │   test_some_util_file.py
    │   test_another_util_file.py
```

To keep things modular and organized, you should place your tool code in the `tool/` folder and your test code in the `tests/` folder. Let's go over the important files:

- **`pyproject.toml`:** This is the Python project file that contains metadata about your project and its dependencies. It is used by [Poetry](https://python-poetry.org/) to install dependencies and manage the tool. Remember to run `poetry install` before starting development to ensure you are working in a clean, stand-alone environment.

- **`README.md`:** This file contains information about your tool, including how to use it, its purpose, environment variables, etc. Be sure to look at existing READMEs for examples.

- **`requirements.txt`:** This file lists just the runtime dependencies for your tool. These should match exactly the non-development dependencies in `pyproject.toml`, excluding the `python` version specification. **You should create this file manually** to ensure it is clean and contains only the necessary runtime dependencies.

- **`.coveragerc`:** This is the coverage configuration file that contains the configuration for the coverage tool. This file is the same across all tools and should always be included.

- **`poetry.lock`:** This is the lock file that contains the exact versions of the dependencies that were installed when `poetry install` was last run. This file should be committed as well to ensure consistency across different environments.

#### Creating `requirements.txt`

Since exporting `requirements.txt` using `poetry export` can sometimes include unnecessary details or development dependencies, it's recommended to create this file manually. Your `requirements.txt` should include all the non-development dependencies specified in your `pyproject.toml`, excluding the `python` version.

**Example `pyproject.toml`:**

```toml
[tool.poetry]
name = "pizza-ordering-tool"
version = "1.0"
description = "A tool for placing and processing pizza orders"
authors = ["Your Name <your.email@example.com>"]
readme = "README.md"
package-mode = false

[tool.poetry.dependencies]
python = ">=3.9,<4.0"
atomic-agents = {path = "../../../", develop = true}
pydantic = ">=2.8.2,<3.0.0"
requests = ">=2.28.0,<3.0.0"

[tool.poetry.group.dev.dependencies]
coverage = ">=7.0.0,<8.0.0"
pytest = ">=8.0.0,<9.0.0"
pytest-cov = ">=5.0.0,<6.0.0"
python-dotenv = ">=1.0.0,<2.0.0"
rich = ">=13.7.0,<14.0.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

**Corresponding `requirements.txt`:**

```
atomic-agents>=1.0.0,<2.0.0
pydantic>=2.8.2,<3.0.0
requests>=2.28.0,<3.0.0
```

**Explanation:**

- The `requirements.txt` includes all the runtime dependencies specified under `[tool.poetry.dependencies]` in `pyproject.toml`, excluding `python`.
- It does **not** include any of the development dependencies specified under `[tool.poetry.group.dev.dependencies]`.
- This manual approach ensures that `requirements.txt` is clean and only contains the necessary packages for running your tool.

### Inheritance and Base Classes

To ensure consistency and interoperability within the Atomic Agents framework, your tool's classes should inherit from specific base classes:

- **Input and Output Schemas:** Must inherit from `BaseIOSchema`.
- **Configuration Class:** Must inherit from `BaseToolConfig`.
- **Main Tool Class:** Must inherit from `BaseTool`.

By adhering to these inheritance rules upfront, you guarantee that your tool aligns with the framework's expectations and can seamlessly integrate with other components.

#### Overriding Title and Description

The `BaseToolConfig` allows you to override the default title and description of your tool. By default, the title and description are derived from the input schema's title and description, so usually, you will not need to set them.

However, there are certain edge cases where you may want to override the title and description, such as when the default title and description are not descriptive or clear enough for your agent.

One example of this could be when you have a tool that performs a web search and another that performs a search in a vector DB filled with internal company documents. You may want to override the title and description of these tools to make it clearer to the LLM that if a question is asked about the company's internal documents, the vector search tool is the appropriate tool to use and not the web search tool.

### Modularity

Each tool should be an independent module that can function on its own. Modularity ensures that tools can be developed, tested, and debugged in isolation, leading to more reliable and maintainable code.

### Reusability

Design tools with reusability in mind. Avoid hardcoding values or making assumptions that limit where and how the tool can be used.

### Single Responsibility Principle

Ensure that each tool does one thing and does it well. This makes your tools easier to understand, test, and maintain.

### Clear Interfaces

Define explicit input and output schemas using Pydantic models. This ensures consistent data handling and makes your tools predictable and reliable.

### Configurability

Provide configuration options to allow users to customize the tool's behavior without modifying the code. Use default values where appropriate to make tools easy to use out of the box.

## Structure

An Atomic Tool in the Atomic Agents framework follows a highly standardized structure. This consistency is crucial for maintainability, interoperability, and ease of understanding.

**The structure of an Atomic Tool includes the following sections, in this specific order:**

1. **Imports**
2. **Input Schema**
3. **Output Schema(s)**
4. **Configuration**
5. **Main Tool & Logic**
6. **Example Usage**

**Remember:** The input and output schemas must always extend from `BaseIOSchema`, and the main tool class must always extend from `BaseTool`.

**Note:** Each section (except imports) should be clearly delineated with a comment block that includes the section's name. For example:

```python
################
# Input Schema #
################
```

Let's explore each of these sections in detail, using our **Pizza Ordering Tool** as the example.

### 1. Imports

All necessary imports should be placed at the top of your script. This includes standard libraries, third-party packages, and modules from the Atomic Agents framework.

**Example:**

```python
import os
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from atomic_agents.agents.base_agent import BaseIOSchema
from atomic_agents.lib.base.base_tool import BaseTool, BaseToolConfig
```

### 2. Input Schema

The **Input Schema** defines the structure and validation rules for the data your tool accepts. It uses Pydantic models to enforce data types, provide default values, and include descriptions.

#### Composing Input Schemas

Input schemas can be composed of multiple models, including Enums and other Pydantic models, to create complex and structured inputs.

**Example:**

```python
################
# Input Schema #
################

class PizzaSize(Enum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"

class CrustType(Enum):
    THIN = "Thin"
    THICK = "Thick"
    STUFFED = "Stuffed"

class Topping(BaseModel):
    name: str = Field(..., description="Name of the topping.")
    extra_cheese: bool = Field(False, description="Add extra cheese to this topping.")

class PizzaOrderInputSchema(BaseIOSchema):
    """
    Captures customer details and order specifics for placing a pizza order.
    """
    customer_name: str = Field(..., description="Name of the customer placing the order.")
    pizza_type: str = Field(..., description="Type of pizza to order (e.g., Margherita, Pepperoni).")
    size: PizzaSize = Field(..., description="Size of the pizza.")
    crust: CrustType = Field(..., description="Type of crust for the pizza.")
    toppings: Optional[List[Topping]] = Field(None, description="List of additional toppings.")
    quantity: int = Field(..., description="Number of pizzas to order.")
```

**Explanation:**

- **Enums:** `PizzaSize` and `CrustType` are Enums that restrict input to predefined choices.
- **Nested Models:** `Topping` is its own Pydantic model used within `PizzaOrderInputSchema`.
- **Fields with Descriptions:** Each field uses `Field` with a description for clarity.
- **Inheritance:** The `PizzaOrderInputSchema` inherits from `BaseIOSchema`.

### 3. Output Schema(s)

The **Output Schema(s)** define the structure of the data your tool outputs. You can have multiple output schemas if your tool produces different types of outputs.

**Example:**

```python
#####################
# Output Schema(s)  #
#####################

class OrderStatus(Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    DELIVERED = "Delivered"

class OrderConfirmationSchema(BaseIOSchema):
    """
    Confirmation details of the placed order.
    """
    order_id: str = Field(..., description="Unique identifier for the order.")
    estimated_delivery_time: str = Field(..., description="Estimated time for order delivery.")
    status: OrderStatus = Field(..., description="Current status of the order.")

class PaymentDetailsSchema(BaseIOSchema):
    """
    Payment information for the order.
    """
    amount: float = Field(..., description="Total amount to be paid.")
    currency: str = Field("USD", description="Currency of the payment.")
    payment_status: str = Field(..., description="Status of the payment (e.g., Paid, Pending).")
```

**Explanation:**

- **Multiple Output Schemas:** Separate schemas for order confirmation and payment details.
- **Enums in Output:** `OrderStatus` Enum represents the status of the order.
- **Inheritance:** Both output schemas inherit from `BaseIOSchema`.

### 4. Configuration

The **Configuration** section allows you to define settings that can customize the tool's behavior.

**Example:**

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
    api_key: str = Field(
        default=os.getenv("PIZZA_API_KEY"),
        description="API key for authenticating with the pizza ordering service."
    )
    title: Optional[str] = Field(
        default="Pizza Ordering Tool",
        description="Override the default title of the tool."
    )
    description: Optional[str] = Field(
        default="A tool to place pizza orders and process payments.",
        description="Override the default description of the tool."
    )
```

**Explanation:**

- **Inheritance:** The configuration class inherits from `BaseToolConfig`.
- **Environment Variables:** Sensitive information like `api_key` is retrieved from environment variables.
- **Title and Description Overrides:** Using `title` and `description` fields to override default values.

### 5. Main Tool & Logic

This is the core of your tool, where you implement the main functionality. Your tool must always have a `run` method, which is the entry point for executing your tool's logic.

**Example:**

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
        """
        Initializes the PizzaOrderingTool with the provided configuration.
        """
        super().__init__(config)
        self.api_endpoint = config.api_endpoint
        self.supported_pizzas = config.supported_pizzas
        self.api_key = config.api_key
        self.tool_name = config.title or self.input_schema.__name__
        self.tool_description = config.description or self.__doc__

    def run(self, params: PizzaOrderInputSchema) -> dict:
        """
        Executes the tool's main logic to place an order and process payment.
        """
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
            estimated_delivery_time=estimated_time,
            status=OrderStatus.CONFIRMED
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
        base_prices = {
            "Margherita": 8.99,
            "Pepperoni": 9.99,
            "Veggie": 10.99,
            "Hawaiian": 9.49
        }
        size_multipliers = {
            PizzaSize.SMALL: 1.0,
            PizzaSize.MEDIUM: 1.2,
            PizzaSize.LARGE: 1.5
        }
        topping_price = 0.99  # Price per additional topping

        base_price = base_prices[params.pizza_type]
        size_multiplier = size_multipliers[params.size]
        toppings_cost = sum(
            topping_price + (0.5 if topping.extra_cheese else 0)
            for topping in params.toppings
        ) if params.toppings else 0

        total = (base_price * size_multiplier + toppings_cost) * params.quantity
        return total

    def process_payment(self, order_id: str, amount: float) -> str:
        """
        Simulates payment processing.
        """
        # Placeholder logic.
        return "Paid"
```

**Explanation:**

- **Inheritance:** The tool class inherits from `BaseTool`.
- **Run Method:** The `run` method is mandatory and serves as the entry point for your tool.
- **Title and Description Overrides:** Uses the configuration's `title` and `description`.
- **Helper Methods:** Break down complex logic into smaller methods for clarity and maintainability.
- **Error Handling:** Validates inputs and raises exceptions where necessary.

### 6. Example Usage

Finally, the **Example Usage** section demonstrates how to instantiate and run your tool. This is invaluable for testing and serves as documentation for users.

**Example:**

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
        size=PizzaSize.MEDIUM,
        crust=CrustType.THIN,
        toppings=[
            Topping(name="Olives", extra_cheese=False),
            Topping(name="Mushrooms", extra_cheese=True)
        ],
        quantity=2
    )

    try:
        outputs = pizza_tool.run(order_input)
        console.print(outputs)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
```

## Best Practices and Guidelines

### Do's

- **Keep Imports at the Top:** Place all import statements at the beginning of your script without a section comment block.
- **Follow the Standard Structure:** Adhere to the prescribed order and format for consistency.
- **Use Clear and Descriptive Names:** Make your code self-explanatory.
- **Document Your Code:** Include docstrings and comments to explain the purpose and functionality.
- **Validate Inputs Thoroughly:** Use Pydantic's features to enforce data integrity.
- **Handle Errors Gracefully:** Provide informative error messages and handle exceptions where appropriate.
- **Keep Functions Small and Focused:** Break down complex logic into helper methods.
- **Commit `poetry.lock`:** Ensure you commit your `poetry.lock` file to maintain consistent dependencies across environments.
- **Manually Create `requirements.txt`:** Ensure your `requirements.txt` file matches the non-development dependencies in your `pyproject.toml`, excluding `python`, and create it manually for clarity.

### Don'ts

- **Don't Hardcode Values:** Use configuration parameters or environment variables instead.
- **Avoid Global Variables:** Keep the state within your tool's scope.
- **Don't Overcomplicate:** Stick to the tool's single responsibility; avoid adding unrelated features.
- **Don't Ignore Security:** Be cautious with sensitive information like API keys; use environment variables.
- **Don't Neglect Performance:** Optimize your code, especially when dealing with large datasets or external API calls.
- **Don't Skip Input Validation:** Never assume inputs are valid; always validate.
- **Don't Auto-Generate `requirements.txt`:** Avoid using automated tools that may include unnecessary or development dependencies; manually specify only the required runtime dependencies.

Best of luck creating your own Atomic Tools!
