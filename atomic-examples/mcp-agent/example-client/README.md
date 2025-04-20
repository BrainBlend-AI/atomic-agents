# MCP Agent Example

This example demonstrates how to build an interactive agent that intelligently selects and uses MCP tools based on user queries. It showcases:

- Dynamic discovery of available MCP tools
- Support for both STDIO and SSE transport methods
- Intelligent tool selection using OpenAI models
- Parameter extraction from natural language queries
- Tool execution with extracted parameters
- Pretty output formatting using Rich

## Features

- **Dual Transport Support**: Use either STDIO or SSE transport for communicating with MCP tools
- **Tool Discovery**: Automatically fetches all available tools from the MCP server
- **Smart Selection**: Uses LLMs to understand user queries and select the most appropriate tool
- **Parameter Extraction**: Extracts tool parameters directly from natural language queries
- **Interactive Chat**: Engage in a continuous conversation, with the agent selecting appropriate tools as needed
- **Rich Output**: Beautiful console output with colors and tables

## Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Set up your OpenAI API key in a `.env` file or as an environment variable:
   ```bash
   export OPENAI_API_KEY=your_api_key
   ```

3. For SSE mode, ensure the MCP server is running at `http://localhost:6969` (default)

4. For STDIO mode, no external server is needed, as the client will launch the appropriate process

## Usage

Run the example with the desired transport method:

```bash
# Default (STDIO mode)
poetry run python -m example_client.main

# Explicitly select STDIO mode
poetry run python -m example_client.main --transport stdio

# Use SSE mode instead
poetry run python -m example_client.main --transport sse
```

The script will:
1. Initialize the appropriate transport method (STDIO or SSE)
2. Fetch all available MCP tools
3. Display them in a table
4. Start an interactive chat session
5. Process your queries, selecting and executing the right tools
6. Clean up resources when you exit

## Transport Methods

### STDIO Transport

STDIO transport launches a local subprocess and communicates with it using standard input/output. This is useful for:

- Local development without a separate server
- Testing new tools
- Offline usage scenarios

Configuration is done in `main_stdio.py` via the `MCPConfig` class:
```python
@dataclass
class MCPConfig:
    openai_model: str = "gpt-4o-mini"
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    mcp_stdio_server_command: str = "poetry run example-mcp-server --mode stdio"
```

### SSE Transport

SSE (Server-Sent Events) transport connects to a remote HTTP server. This is useful for:

- Production deployments
- Sharing tools across multiple clients
- Centralized tool management

Configuration is done in `main_sse.py` via the `MCPConfig` class:
```python
@dataclass
class MCPConfig:
    mcp_server_url: str = "http://localhost:6969"
    openai_model: str = "gpt-4o-mini"
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
```

## Agent Logic

The agent uses several key components:

1. **Orchestrator Agent**: Analyzes queries and determines which tool to use or when to provide a direct response
2. **Tool Factory**: Fetches and instantiates appropriate tool classes
3. **Memory**: Maintains conversation history for context-aware responses
4. **System Prompt Generator**: Creates optimized prompts for the LLM

## Interactive Chat

During the interactive session, you can:

- Ask natural language questions
- Request specific calculations or operations
- Get direct answers for simple queries
- See which tools are being selected and why
- Exit by typing 'exit' or 'quit'

## Example Queries

Try queries like:

- "What is 2+2?"
- "Please calculate the square root of 144"
- "Can you tell me what time it is?"
- "Generate a random number between 1 and 100"
- "plz do the sum of (59-33) and (33*0.123) and then multiply that by 0.99, take that, and square it"

## Extending

To extend this example:

1. Add new tools to your MCP server
2. Configure either the STDIO command or SSE server URL in the config
3. Customize the agent's system prompt in the `SystemPromptGenerator`

## Requirements

- Python 3.9+
- OpenAI API key
- Poetry for dependency management
- For SSE mode: MCP server running at configured URL (default: http://localhost:6969)

## Code Structure

- `main.py`: Entry point that parses arguments and selects the appropriate transport
- `main_stdio.py`: Implementation using STDIO transport
- `main_sse.py`: Implementation using SSE transport
- `example-mcp-server/`: Example server implementation

---

**This example is intended for educational and demonstration purposes.**
