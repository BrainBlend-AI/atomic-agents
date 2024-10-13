# Atomic Agents
<img src="./.assets/logo.png" alt="Atomic Agents" width="600"/>

[![PyPI version](https://badge.fury.io/py/atomic-agents.svg)](https://badge.fury.io/py/atomic-agents)

The Atomic Agents framework is designed to be modular, extensible, and easy to use. The main goal of the framework is to get rid of redundant complexity, unnecessary abstractions, and hidden assumptions while still providing a flexible and powerful framework for building AI applications through atomicity. The resulting framework provides a set of tools and agents that can be combined to create powerful applications. The framework is built on top of [Instructor](https://github.com/jxnl/instructor) and leverages the power of [Pydantic](https://docs.pydantic.dev/latest/) for data/schema validation and serialization.

<!-- ![alt text](./.assets/architecture_highlevel_overview.png) -->
<img src="./.assets/architecture_highlevel_overview.png" alt="High-level architecture overview of Atomic Agents" width="600"/>
<img src="./.assets/what_is_sent_in_prompt.png" alt="Diagram showing what is sent to the LLM in the prompt" width="600"/>

## Installation
To install Atomic Agents, you can use pip:

```bash
pip install atomic-agents
```

This also installs the CLI *Atomic Assembler* which can be used to download Tools (and soon also Agents and Pipelines).

## Quickstart & Examples
A complete list of examples can be found in the [examples](./atomic-examples/) directory.

We do our best to thoroughly document each example, but if something is unclear, please don't hesitate to open an issue or a pull request in order to improve the documentation.

Here's a quick snippet demonstrating how easy it is to create a powerful agent with Atomic Agents:

```python
# Define a custom output schema
class CustomOutputSchema(BaseIOSchema):
    chat_message: str = Field(..., description="The chat message from the agent.")
    suggested_questions: List[str] = Field(..., description="Suggested follow-up questions.")

# Set up the system prompt
system_prompt_generator = SystemPromptGenerator(
    background=["This assistant is knowledgeable, helpful, and suggests follow-up questions."],
    steps=[
        "Analyze the user's input to understand the context and intent.",
        "Formulate a relevant and informative response.",
        "Generate 3 suggested follow-up questions for the user."
    ],
    output_instructions=[
        "Provide clear and concise information in response to user queries.",
        "Conclude each response with 3 relevant suggested questions for the user."
    ]
)

# Initialize the agent
agent = BaseAgent(
    config=BaseAgentConfig(
        client=your_openai_client,  # Replace with your actual client
        model="gpt-4",
        system_prompt_generator=system_prompt_generator,
        memory=AgentMemory(),
        output_schema=CustomOutputSchema
    )
)

# Use the agent
response = agent.run(user_input)
print(f"Agent: {response.chat_message}")
print("Suggested questions:")
for question in response.suggested_questions:
    print(f"- {question}")
```

This snippet showcases how to create a customizable agent that responds to user queries and suggests follow-up questions. For full, runnable examples, please refer to the following files in the `atomic-examples/quickstart/quickstart/` directory:

- [1_basic_chatbot.py](./atomic-examples/quickstart/quickstart/1_basic_chatbot.py): A minimal chatbot example to get you started.
- [2_basic_custom_chatbot.py](./atomic-examples/quickstart/quickstart/2_basic_custom_chatbot.py): A more advanced example with a custom system prompt.
- [3_basic_custom_chatbot_with_custom_schema.py](./atomic-examples/quickstart/quickstart/3_basic_custom_chatbot_with_custom_schema.py): A more advanced example with a custom output schema.
- [4_basic_chatbot_different_providers.py](./atomic-examples/quickstart/quickstart/4_basic_chatbot_different_providers.py): Demonstrates how to use different providers like Ollama or Groq.

These examples provide a great starting point for understanding and using Atomic Agents.

## Running the CLI
To run the CLI simply run the following command:

```bash
atomic
```

After running this command you should be presented with a menu, allowing you to download Tools.
<img src="./.assets/atomic-cli.png" alt="Atomic CLI menu" width="400"/>

## Provider & Model Compatibility
Atomic Agents depends on the [Instructor](https://github.com/jxnl/instructor) package. This means that in all examples where OpenAI is used, any other API supported by Instructor can be used, such as Ollama, Groq, Mistral, Cohere, Anthropic, Gemini, and more. For a complete list please refer to the instructor documentation on its [GitHub page](https://github.com/jxnl/instructor).

## Contributing
We welcome contributions! Please follow these steps to contribute:

See the [Developer Guide](./DEV_GUIDE.md) for more information on how to contribute to Atomic Agents.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=BrainBlend-AI/atomic-agents&type=Date)](https://star-history.com/#BrainBlend-AI/atomic-agents&Date)
