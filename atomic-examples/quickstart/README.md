# Atomic Agents Quickstart Examples

This directory contains quickstart examples for the Atomic Agents project. These examples demonstrate various features and capabilities of the Atomic Agents framework.

## Getting Started

To run these examples:

1. Clone the main Atomic Agents repository:

   ```bash
   git clone https://github.com/BrainBlend-AI/atomic-agents
   ```

2. Navigate to the quickstart directory:

   ```bash
   cd atomic-agents/atomic-examples/quickstart
   ```

3. Install the dependencies using uv:

   ```bash
   uv sync
   ```

4. Run the examples using uv:

   ```bash
   uv run python quickstart/1_0_basic_chatbot.py
   ```

## Example Files

### 1_0. Basic Chatbot (1_0_basic_chatbot.py)

This example demonstrates a simple chatbot using the Atomic Agents framework. It includes:

- Setting up the OpenAI API client
- Initializing a basic agent with default configurations
- Running a chat loop where the user can interact with the agent

### 1_1. Basic Streaming Chatbot (1_1_basic_chatbot_streaming.py)

This example is similar to 1_0 but it uses `run_stream` method.

### 1_2. Basic Async Streaming Chatbot (1_2_basic_chatbot_async_streaming.py)

This example is similar to 1_0 but it uses an async client and `run_async_stream` method.

### 2. Custom Chatbot (2_basic_custom_chatbot.py)

This example shows how to create a custom chatbot with:

- A custom system prompt
- Customized agent configuration
- A chat loop with rhyming responses

### 3_0. Custom Chatbot with Custom Schema (3_0_basic_custom_chatbot_with_custom_schema.py)

This example demonstrates:

- Creating a custom output schema for the agent
- Implementing suggested follow-up questions in the agent's responses
- Using a custom system prompt and agent configuration

### 3_1. Custom Streaming Chatbot with Custom Schema

This example is similar to 3_0 but uses an async client and `run_async_stream` method.

### 4. Chatbot with Different Providers (4_basic_chatbot_different_providers.py)

This example showcases:

- How to use different AI providers (OpenAI, Groq, Ollama)
- Dynamically selecting a provider at runtime
- Adapting the agent configuration based on the chosen provider

### 5. Custom System Role (5_custom_system_role_for_reasoning_models.py)

This example showcases a usage of `system_role` parameter for a reasoning model.

### 6_0. Asynchronous Processing (6_0_asynchronous_processing.py)

This example showcases a utilization of `run_async` method for a concurrent processing of multiple data.

### 6_1. Asynchronous Streaming Processing

This example adds streaming to 6_0.

## Running the Examples

To run any of the examples, use the following command:

```bash
uv run python quickstart/<example_file_name>.py
```

Replace `<example_file_name>` with the name of the example you want to run (e.g., `1_basic_chatbot.py`).

These examples provide a great starting point for understanding and working with the Atomic Agents framework. Feel free to modify and experiment with them to learn more about the capabilities of Atomic Agents.
