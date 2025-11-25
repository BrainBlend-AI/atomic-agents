# Example MCP Server

This project is an MCP (Model Context Protocol) server that provides tools and resources to be used by MCP clients. It supports both STDIO and SSE (HTTP) transport methods, making it versatile for different deployment scenarios.

## Project Structure

```
./
├── example_mcp_server/           # Python package for your server code
│   ├── __init__.py              # Package initialization
│   ├── server.py                # Unified server entry point with mode selection
│   ├── server_stdio.py          # Implementation for stdio transport
│   ├── server_sse.py            # Implementation for SSE transport (HTTP)
│   ├── server_http.py           # Implementation for HTTP Stream transport
│   ├── interfaces/              # Base classes/interfaces for tools and resources
│   │   ├── __init__.py
│   │   ├── resource.py
│   │   └── tool.py
│   ├── resources/               # Implementation of resources
│   │   ├── __init__.py
│   │   ├── hello_world.py       # Example static resource
│   │   └── user_profile.py      # Example dynamic resource with URI parameters
│   ├── services/                # Services for managing tools and resources
│   │   ├── __init__.py
│   │   ├── resource_service.py  # Handles resource registration and routing
│   │   └── tool_service.py      # Handles tool registration and execution
│   └── tools/                   # Implementation of tools
│       ├── __init__.py
│       └── hello_world.py       # Example tool with input/output schemas
├── pyproject.toml               # Project metadata and dependencies
└── README.md                    # This file
```

## Setup

1. **Navigate** into the project directory:
   ```bash
   cd atomic-examples/mcp-agent/example-mcp-server
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

## Running the Server

The server can run in three modes: `stdio` (standard input/output), `sse` (HTTP Server-Sent Events), or `http` (HTTP Stream Transport). You must specify the desired mode using the `--mode` parameter.

### Using the Command Line Script

After installation, you can use the `example-mcp-server` command directly:

```bash
# Run in stdio mode (for direct subprocess communication)
uv run example-mcp-server --mode=stdio

# Run in SSE mode (defaults to http://0.0.0.0:6969)
uv run example-mcp-server --mode=sse

# Run in SSE mode with custom host/port
uv run example-mcp-server --mode=sse --host 127.0.0.1 --port 8000

# Run in SSE mode with auto-reload for development
uv run example-mcp-server --mode=sse --reload

# Run in HTTP Stream mode (default http://0.0.0.0:6969/mcp)
uv run example-mcp-server --mode=http_stream

# Run in HTTP Stream mode with custom host/port
uv run example-mcp-server --mode=http_stream --host 127.0.0.1 --port 8000

# Run in HTTP Stream mode with auto-reload
uv run example-mcp-server --mode=http_stream --reload
```

### Using Python Module

Alternatively, you can run the server as a Python module:

```bash
# Using the unified server script
uv run python -m example_mcp_server.server --mode=stdio
uv run python -m example_mcp_server.server --mode=sse
uv run python -m example_mcp_server.server --mode=http_stream

# Or call the specific implementations directly
uv run python -m example_mcp_server.server_stdio
uv run python -m example_mcp_server.server_sse
uv run python -m example_mcp_server.server_http
```

## Client Integration

This server is designed to work with the companion MCP client in the `example-client` directory. The client can connect to this server using either:

1. **STDIO Transport**: The client launches this server as a subprocess and communicates through standard input/output
2. **SSE Transport**: The client connects to this server running as an HTTP service
3. **HTTP Stream Transport**: The client connects to the `/mcp` endpoint for a streaming RPC-like interface

### STDIO Mode Connection

In STDIO mode, the client launches the server using a command like:

```python
mcp_stdio_server_command: str = "uv run example-mcp-server --mode stdio"
```

This mode is useful for local development, testing, and when you don't want to run a separate server process.

### SSE Mode Connection

In SSE mode, the client connects to the server over HTTP:

```python
mcp_server_url: str = "http://localhost:6969"
```

This mode is better for production deployments, sharing tools across multiple clients, or when the server needs to run on a different machine.

### HTTP Stream Mode Connection

In HTTP Stream mode, the client connects to the server's `/mcp` endpoint:

```python
mcp_server_url: str = "http://localhost:6969/mcp"
```

This mode supports a streaming RPC-like interaction over HTTP, where the client can negotiate a session, send JSON-RPC calls, and terminate the session.

## Developing Your Server

### Development Mode with Auto-Reload

For faster development with the SSE mode, you can use the auto-reload feature which automatically restarts the server when code changes are detected:

```bash
uv run example-mcp-server --mode=sse --reload
```

This is particularly useful during active development as you won't need to manually restart the server after each code change.

### Adding New Tools

1. **Create a new Python file** in the `example_mcp_server/tools/` directory (e.g., `my_tool.py`).
2. **Define your tool class** inheriting from `Tool` (from `example_mcp_server.interfaces.tool`).
3. **Define an input model** inheriting from `BaseToolInput` for your tool's parameters using Pydantic.
4. **Implement the `execute` method** containing your tool's logic.
5. **Import and add your tool class** to the `__all__` list in `example_mcp_server/tools/__init__.py`.
6. **Instantiate your tool** in the `get_available_tools` function within `example_mcp_server/server_stdio.py` and `example_mcp_server/server_sse.py`.

### Adding New Resources

1. **Create a new Python file** in the `example_mcp_server/resources/` directory (e.g., `my_resource.py`).
2. **Define your resource class** inheriting from `Resource` (from `example_mcp_server.interfaces.resource`).
3. **Define the required class attributes**: `name`, `description`, `uri`, `mime_type`.
4. **Implement the `read` method**. For dynamic URIs (e.g., `data://{item_id}`), parameters are passed as keyword arguments to `read` (e.g., `read(item_id=...)`).
5. **Import and add your resource class** to the `__all__` list in `example_mcp_server/resources/__init__.py`.
6. **Instantiate your resource** in the `get_available_resources` function within `example_mcp_server/server_stdio.py` and `example_mcp_server/server_sse.py`.

## Service Layer

- `ToolService`: Manages the registration and execution of tools. It dynamically creates handler functions based on tool input schemas.
- `ResourceService`: Manages the registration and reading of resources. It handles routing for static and dynamic URIs.

## Learn More About MCP

Visit the official [Model Context Protocol Documentation](https://modelcontextprotocol.io/) for detailed information about the protocol, concepts, and advanced features.
