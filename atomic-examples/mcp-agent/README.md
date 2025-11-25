# MCP Agent Example

This directory contains a complete example of a Model Context Protocol (MCP) implementation, including both client and server components. It demonstrates how to build an intelligent agent that leverages MCP tools via different transport methods.

## Components

This example consists of two main components:

### 1. Example Client (`example-client/`)

An interactive agent that:

- Connects to MCP servers using multiple transport methods (STDIO, SSE, HTTP Stream)
- Dynamically discovers available tools
- Processes natural language queries
- Selects appropriate tools based on user intent
- Executes tools with extracted parameters (sync and async)
- Provides responses in a conversational format

The client features a universal launcher that supports multiple implementations:
- **stdio**: Blocking STDIO CLI client (default)
- **stdio_async**: Async STDIO client
- **sse**: SSE CLI client
- **http_stream**: HTTP Stream CLI client
- **fastapi**: FastAPI HTTP API server

[View Example Client README](example-client/README.md)

### 2. Example MCP Server (`example-mcp-server/`)

A server that:

- Provides MCP tools and resources
- Supports both STDIO and SSE (HTTP) transport methods
- Includes example tools for demonstration
- Can be extended with custom functionality
- Features auto-reload for development

[View Example MCP Server README](example-mcp-server/README.md)

## Understanding the Example

This example shows the flexibility of the MCP architecture with two distinct transport methods:

### STDIO Transport

- The client launches the server as a subprocess
- Communication occurs through standard input/output
- No network connectivity required
- Good for local development and testing

### SSE Transport

- The server runs as a standalone HTTP service
- The client connects via Server-Sent Events (SSE)
- Multiple clients can connect to one server
- Better for production deployments

### HTTP Stream Transport

- The server exposes a single `/mcp` HTTP endpoint for session negotiation, JSON-RPC calls, and termination
- Supports GET (stream/session ID), POST (JSON-RPC payloads), and DELETE (session cancel)
- Useful for HTTP clients that prefer a single transport endpoint

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/BrainBlend-AI/atomic-agents
   cd atomic-agents/atomic-examples/mcp-agent
   ```

2. Set up the server:

   ```bash
   cd example-mcp-server
   uv sync
   ```

3. Set up the client:
   ```bash
   cd ../example-client
   uv sync
   ```

4. Run the example:

   **Using STDIO transport (default):**

   ```bash
   cd example-client
   uv run python -m example_client.main --client stdio
   # or simply:
   uv run python -m example_client.main
   ```

   **Using async STDIO transport:**

   ```bash
   cd example-client
   uv run python -m example_client.main --client stdio_async
   ```

   **Using SSE transport (Deprecated):**

   ```bash
   # First terminal: Start the server
   cd example-mcp-server
   uv run python -m example_mcp_server.server --mode=sse

   # Second terminal: Run the client with SSE transport
   cd example-client
   uv run python -m example_client.main --client sse
   ```

   **Using HTTP Stream transport:**

   ```bash
   # First terminal: Start the server
   cd example-mcp-server
   uv run python -m example_mcp_server.server --mode=http_stream

   # Second terminal: Run the client with HTTP Stream transport
   cd example-client
   uv run python -m example_client.main --client http_stream
   ```

   **Using FastAPI client:**

   ```bash
   # First terminal: Start the MCP server
   cd example-mcp-server
   uv run python -m example_mcp_server.server --mode=http_stream

   # Second terminal: Run the FastAPI client
   cd example-client
   uv run python -m example_client.main --client fastapi
   # Then visit http://localhost:8000 for the API interface
   ```

**Note:** When using SSE, FastAPI or HTTP Stream transport, make sure the server is running before starting the client. The server runs on port 6969 by default.

## Example Queries

The example includes a set of basic arithmetic tools that demonstrate the agent's capability to break down and solve complex mathematical expressions:

### Available Demo Tools

- **AddNumbers**: Adds two numbers together (number1 + number2)
- **SubtractNumbers**: Subtracts the second number from the first (number1 - number2)
- **MultiplyNumbers**: Multiplies two numbers together (number1 * number2)
- **DivideNumbers**: Divides the first number by the second (handles division by zero)

### Conversation Flow

When you interact with the agent, it:

1. Analyzes your input to break it down into sequential operations
2. Selects appropriate tools for each operation
3. Shows its reasoning for each tool selection
4. Executes the tools in sequence
5. Maintains context between operations to build up the final result

For example, when calculating `(5-9)*0.123`:

1. First uses `SubtractNumbers` to compute (5-9) = -4
2. Then uses `MultiplyNumbers` to compute (-4 * 0.123) = -0.492
3. Provides the final result with clear explanation

For more complex expressions like `((4**3)-10)/100)**2`, the agent:

1. Breaks down the expression into multiple steps
2. Uses `MultiplyNumbers` repeatedly for exponentiation (4**3)
3. Uses `SubtractNumbers` for the subtraction operation
4. Uses `DivideNumbers` for division by 100
5. Uses `MultiplyNumbers` again for the final squaring operation

Each step in the conversation shows:

- The tool being executed
- The parameters being used
- The intermediate result
- The agent's reasoning for the next step

Try queries like:

```python
# Simple arithmetic
"What is 2+2?"
# Uses AddNumbers tool directly

# Complex expressions
"(5-9)*0.123"
# Uses SubtractNumbers followed by MultiplyNumbers

# Multi-step calculations
"((4**3)-10)/100)**2"
# Uses multiple tools in sequence to break down the complex expression

# Natural language queries
"Calculate the difference between 50 and 23, then multiply it by 3"
# Understands natural language and breaks it down into appropriate tool calls
```

## Learn More

- [Atomic Agents Documentation](https://github.com/BrainBlend-AI/atomic-agents)
- [Model Context Protocol](https://modelcontextprotocol.io/)
