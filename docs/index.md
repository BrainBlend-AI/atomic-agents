# Welcome to Atomic Agents Documentation

```{toctree}
:maxdepth: 2
:caption: Documentation

guides/index
api/index
examples/index
contributing
```

# A Lightweight and Modular Framework for Building AI Agents

![Atomic Agents](_static/logo.png)

The Atomic Agents framework is designed around the concept of atomicity to be an extremely lightweight and modular framework for building Agentic AI pipelines and applications without sacrificing developer experience and maintainability. The framework provides a set of tools and agents that can be combined to create powerful applications. It is built on top of [Instructor](https://github.com/jxnl/instructor) and leverages the power of [Pydantic](https://docs.pydantic.dev/latest/) for data and schema validation and serialization.

All logic and control flows are written in Python, enabling developers to apply familiar best practices and workflows from traditional software development without compromising flexibility or clarity.

## Key Features

- **Modularity**: Build AI applications by combining small, reusable components
- **Predictability**: Define clear input and output schemas using Pydantic
- **Extensibility**: Easily swap out components or integrate new ones
- **Control**: Fine-tune each part of the system individually
- **Provider Agnostic**: Works with various LLM providers through Instructor
- **Built for Production**: Robust error handling and async support

## Installation

You can install Atomic Agents using pip:

```bash
pip install atomic-agents
```

Or using Poetry (recommended):

```bash
poetry add atomic-agents
```

Make sure you also install the provider you want to use. For example, to use OpenAI and Groq:

```bash
pip install openai groq
```

This also installs the CLI *Atomic Assembler*, which can be used to download Tools (and soon also Agents and Pipelines).

```{note}
The framework supports multiple providers through Instructor, including **OpenAI**, **Anthropic**, **Groq**, **Ollama** (local models), **Gemini**, and more!
For a full list of all supported providers and their setup instructions, have a look at the [Instructor Integrations documentation](https://python.useinstructor.com/integrations/).
```

## Quick Example

Here's a glimpse of how easy it is to create an agent:

```python
import instructor
import openai
from atomic_agents.lib.components.agent_memory import AgentMemory
from atomic_agents.agents.base_agent import BaseAgent, BaseAgentConfig, BaseAgentInputSchema


# Set up your API key (either in environment or pass directly)
# os.environ["OPENAI_API_KEY"] = "your-api-key"
# or pass it to the client: openai.OpenAI(api_key="your-api-key")

# Initialize agent with memory
memory = AgentMemory()

# Set up client with your preferred provider
client = instructor.from_openai(openai.OpenAI())  # Pass your API key here if not in environment

# Create an agent
agent = BaseAgent(
    config=BaseAgentConfig(
        client=client,
        model="gpt-4o-mini",  # Use your provider's model
        memory=memory
    )
)

# Interact with your agent (using the agent's input schema)
response = agent.run(agent.input_schema(chat_message="Tell me about quantum computing"))

# Or more explicitly:
response = agent.run(
    BaseAgentInputSchema(chat_message="Tell me about quantum computing")
)

print(response)
```

## Example Projects

Check out our example projects in our [GitHub repository](https://github.com/BrainBlend-AI/atomic-agents/tree/main/atomic-examples):

- [Quickstart Examples](https://github.com/BrainBlend-AI/atomic-agents/tree/main/atomic-examples/quickstart): Simple examples to get started
- [Basic Multimodal](https://github.com/BrainBlend-AI/atomic-agents/tree/main/atomic-examples/basic-multimodal): Analyze images with text
- [RAG Chatbot](https://github.com/BrainBlend-AI/atomic-agents/tree/main/atomic-examples/rag-chatbot): Build context-aware chatbots
- [Web Search Agent](https://github.com/BrainBlend-AI/atomic-agents/tree/main/atomic-examples/web-search-agent): Create agents that perform web searches
- [Deep Research](https://github.com/BrainBlend-AI/atomic-agents/tree/main/atomic-examples/deep-research): Perform deep research tasks
- [YouTube Summarizer](https://github.com/BrainBlend-AI/atomic-agents/tree/main/atomic-examples/youtube-summarizer): Extract knowledge from videos
- [YouTube to Recipe](https://github.com/BrainBlend-AI/atomic-agents/tree/main/atomic-examples/youtube-to-recipe): Convert cooking videos into structured recipes
- [Orchestration Agent](https://github.com/BrainBlend-AI/atomic-agents/tree/main/atomic-examples/orchestration-agent): Coordinate multiple agents for complex tasks

## Community & Support

- [GitHub Repository](https://github.com/BrainBlend-AI/atomic-agents)
- [Issue Tracker](https://github.com/BrainBlend-AI/atomic-agents/issues)
- [Reddit Community](https://www.reddit.com/r/AtomicAgents/)

## Indices and References

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
