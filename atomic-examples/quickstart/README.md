# Atomic Agents Quickstart Examples

This directory contains quickstart examples for the Atomic Agents project. These examples demonstrate various features and capabilities of the Atomic Agents framework.

## Getting Started

To run these examples:

1. Clone the main Atomic Agents repository:
   ```
   git clone https://github.com/BrainBlend-AI/atomic-agents
   ```

2. Navigate to the quickstart directory:
   ```
   cd atomic-agents/atomic-examples/quickstart
   ```

3. Install the dependencies using Poetry:
   ```
   poetry install
   ```

4. Run the examples using Poetry:
   ```
   poetry run python quickstart/1_basic_chatbot.py
   ```

## Example Files

### 1. Basic Chatbot (1_basic_chatbot.py)

This example demonstrates a simple chatbot using the Atomic Agents framework. It includes:
- Setting up the OpenAI API client
- Initializing a basic agent with default configurations
- Running a chat loop where the user can interact with the agent

### 2. Custom Chatbot (2_basic_custom_chatbot.py)

This example shows how to create a custom chatbot with:
- A custom system prompt
- Customized agent configuration
- A chat loop with rhyming responses

### 3. Custom Chatbot with Custom Schema (3_basic_custom_chatbot_with_custom_schema.py)

This example demonstrates:
- Creating a custom output schema for the agent
- Implementing suggested follow-up questions in the agent's responses
- Using a custom system prompt and agent configuration

### 4. Chatbot with Different Providers (4_basic_chatbot_different_providers.py)

This example showcases:
- How to use different AI providers (OpenAI, Groq, Ollama)
- Dynamically selecting a provider at runtime
- Adapting the agent configuration based on the chosen provider

## Running the Examples

To run any of the examples, use the following command:

```
poetry run python quickstart/<example_file_name>.py
```

Replace `<example_file_name>` with the name of the example you want to run (e.g., `1_basic_chatbot.py`).

These examples provide a great starting point for understanding and working with the Atomic Agents framework. Feel free to modify and experiment with them to learn more about the capabilities of Atomic Agents.
