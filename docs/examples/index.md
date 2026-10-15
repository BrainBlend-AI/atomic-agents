# Example Projects

This section contains detailed examples of using Atomic Agents in various scenarios.

```{note}
All examples are available in optimized formats for AI assistants:
- **{download}`Examples with documentation <../_static/llms-examples.txt>`** - All examples with source code and READMEs
- **{download}`Full framework package <../_static/llms-full.txt>`** - Complete documentation, source, and examples
```

## Quickstart Examples

Simple examples to get started with the framework:

- Basic chatbot with history
- Custom chatbot with personality
- Streaming responses
- Custom input/output schemas
- Multiple provider support

📂 **[View on GitHub](https://github.com/eigenwise/atomic-agents/tree/main/atomic-examples/quickstart)** - Browse the complete source code and run the examples

## Hooks System

Comprehensive monitoring and error handling with the AtomicAgent hook system:

- Parse error handling and validation
- API call monitoring and metrics
- Response time tracking and performance analysis
- Intelligent retry mechanisms
- Production-ready error isolation
- Real-time performance dashboards

📂 **[View on GitHub](https://github.com/eigenwise/atomic-agents/tree/main/atomic-examples/hooks-example)** - Browse the complete source code and run the examples

## Phoenix Tracing

Trace agents and tools in Arize Phoenix with the optional OpenInference instrumentor:

- Automatic AGENT and TOOL spans via `phoenix.otel.register(auto_instrument=True)`
- LLM spans from the OpenAI instrumentor nested under each agent run
- A parent chain span that ties a planner agent, a calculator tool and an answer agent into one trace
- Session grouping with `using_session`

📂 **[View on GitHub](https://github.com/eigenwise/atomic-agents/tree/main/atomic-examples/phoenix-tracing)** - Browse the complete source code and run the examples

## Basic Multimodal

Examples of working with images and text:

- Image analysis with text descriptions
- Image-based question answering
- Visual content generation
- Multi-image comparisons

📂 **[View on GitHub](https://github.com/eigenwise/atomic-agents/tree/main/atomic-examples/basic-multimodal)** - Browse the complete source code and run the examples

## RAG Chatbot

Build context-aware chatbots with retrieval-augmented generation:

- Document indexing and embedding
- Semantic search integration
- Context-aware responses
- Source attribution
- Follow-up suggestions

📂 **[View on GitHub](https://github.com/eigenwise/atomic-agents/tree/main/atomic-examples/rag-chatbot)** - Browse the complete source code and run the examples

## Web Search Agent

Create agents that can search and analyze web content:

- Web search integration
- Content extraction
- Result synthesis
- Multi-source research
- Citation tracking

📂 **[View on GitHub](https://github.com/eigenwise/atomic-agents/tree/main/atomic-examples/web-search-agent)** - Browse the complete source code and run the examples

## Deep Research

Perform comprehensive research tasks:

- Multi-step research workflows
- Information synthesis
- Source validation
- Structured output generation
- Citation management

📂 **[View on GitHub](https://github.com/eigenwise/atomic-agents/tree/main/atomic-examples/deep-research)** - Browse the complete source code and run the examples

## YouTube Summarizer

Extract and analyze information from videos:

- Transcript extraction
- Content summarization
- Key point identification
- Timestamp linking
- Chapter generation

📂 **[View on GitHub](https://github.com/eigenwise/atomic-agents/tree/main/atomic-examples/youtube-summarizer)** - Browse the complete source code and run the examples

## YouTube to Recipe

Convert cooking videos into structured recipes:

- Video analysis
- Recipe extraction
- Ingredient parsing
- Step-by-step instructions
- Time and temperature conversion

📂 **[View on GitHub](https://github.com/eigenwise/atomic-agents/tree/main/atomic-examples/youtube-to-recipe)** - Browse the complete source code and run the examples

## Orchestration Agent

Coordinate multiple agents for complex tasks:

- Agent coordination
- Task decomposition
- Progress tracking
- Error handling
- Result aggregation

📂 **[View on GitHub](https://github.com/eigenwise/atomic-agents/tree/main/atomic-examples/orchestration-agent)** - Browse the complete source code and run the examples

## MCP Agent

Build intelligent agents using the Model Context Protocol:

- Server implementation with multiple transport methods
- Dynamic tool discovery and registration
- Natural language query processing
- Stateful conversation handling
- Extensible tool architecture

[View MCP Agent Documentation](mcp_agent.md)
📂 **[View on GitHub](https://github.com/eigenwise/atomic-agents/tree/main/atomic-examples/mcp-agent)** - Browse the complete source code and run the examples
