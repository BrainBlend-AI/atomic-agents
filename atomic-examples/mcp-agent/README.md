# MCP Agent Example

This directory contains a complete example of a Model Context Protocol (MCP) implementation, including both client and server components. It demonstrates how to build an intelligent agent that leverages MCP tools via different transport methods.

## Components

This example consists of two main components:

### 1. Example Client (`example-client/`)

An interactive agent that:
- Connects to MCP servers using either STDIO or SSE transport
- Dynamically discovers available tools
- Processes natural language queries
- Selects appropriate tools based on user intent
- Executes tools with extracted parameters
- Provides responses in a conversational format

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

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/BrainBlend-AI/atomic-agents
   cd atomic-agents/atomic-examples/mcp-agent
   ```

2. Set up the server:
   ```bash
   cd example-mcp-server
   poetry install
   ```

3. Set up the client:
   ```bash
   cd ../example-client
   poetry install
   ```

4. Run the example:

   **Using STDIO transport (default):**
   ```bash
   cd example-client
   poetry run python -m example_client.main
   ```

   **Using SSE transport:**
   ```bash
   # First terminal: Start the server
   cd example-mcp-server
   poetry run example-mcp-server --mode=sse

   # Second terminal: Run the client
   cd example-client
   poetry run python -m example_client.main --transport sse
   ```

## Example Queries

Try queries like:

- "What is 2+2?"
- "Please calculate the square root of 144"
- "Can you tell me what time it is?"
- "Generate a random number between 1 and 100"
- "plz do the sum of (59-33) and (33*0.123) and then multiply that by 0.99, take that, and square it"

## Learn More

- [Atomic Agents Documentation](https://github.com/BrainBlend-AI/atomic-agents)
- [Model Context Protocol](https://modelcontextprotocol.io/)
