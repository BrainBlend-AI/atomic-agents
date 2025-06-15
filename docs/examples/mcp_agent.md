# MCP Server and Client Example

This guide provides a detailed overview of the Model Context Protocol (MCP) server and client example implementation in the Atomic Agents framework.

## Overview

The MCP example demonstrates how to build an intelligent agent system using the Model Context Protocol, showcasing both server and client implementations. The example supports three transport methods: STDIO, Server-Sent Events (SSE), and HTTP Stream.

## Architecture

### MCP Server

The server component (`example-mcp-server`) is built using:
- FastMCP: A high-performance MCP server implementation
- Starlette: A lightweight ASGI framework
- Uvicorn: An ASGI server implementation

Key components:
1. **Transport Layers**:
   - `server_stdio.py`: Implements STDIO-based communication
   - `server_sse.py`: Implements SSE-based HTTP communication
   - `server_http.py`: Implements unified HTTP streaming transport 

2. **Tools Service**:
   - Manages registration and execution of MCP tools
   - Handles tool discovery and metadata

3. **Resource Service**:
   - Manages static resources
   - Handles resource discovery and access

4. **Built-in Tools**:
   - `AddNumbersTool`: Performs addition
   - `SubtractNumbersTool`: Performs subtraction
   - `MultiplyNumbersTool`: Performs multiplication
   - `DivideNumbersTool`: Performs division

### MCP Client

The client component (`example-client`) is an intelligent agent that:

1. **Tool Discovery**:
   - Dynamically discovers available tools from the MCP server
   - Builds a schema-based tool registry

2. **Query Processing**:
   - Uses GPT models for natural language understanding
   - Extracts parameters from user queries
   - Selects appropriate tools based on intent

3. **Execution Flow**:
   - Maintains conversation context
   - Handles tool execution results
   - Provides conversational responses

## Implementation Details

### Server Implementation

The server supports three transport methods:

1. **SSE Transport** (`server_sse.py`):
```python
# Initialize FastMCP server
mcp = FastMCP("example-mcp-server")

# Register tools and resources
tool_service.register_tools(get_available_tools())
resource_service.register_resources(get_available_resources())

# Create Starlette app with CORS support
app = create_starlette_app(mcp_server)
```

2. **STDIO Transport** (`server_stdio.py`):
- Runs as a subprocess
- Communicates through standard input/output
- Ideal for local development

3. **HTTP Stream Transport** (`server_http.py`):
- Single `/mcp` endpoint for JSON-RPC and SSE-style streaming
- Handles session via `Mcp-Session-Id` header; allows resumable and cancelable streams

### Client Implementation

The client uses a sophisticated orchestration system:

1. **Tool Management**:
```python
# Fetch available tools
tools = fetch_mcp_tools(
    mcp_endpoint=config.mcp_server_url,
    use_stdio=False,
)

# Build tool schema mapping
tool_schema_to_class_map = {
    ToolClass.input_schema: ToolClass
    for ToolClass in tools
    if hasattr(ToolClass, "input_schema")
}
```

2. **Query Processing**:
- Uses an orchestrator agent to analyze queries
- Extracts parameters and selects appropriate tools
- Maintains conversation context through ChatHistory

## MCP Transport Methods

The example implements two distinct transport methods, each with its own advantages:

### 1. STDIO Transport

STDIO transport uses standard input/output streams for communication between the client and server:

```python
# Client-side STDIO setup (from main_stdio.py)
async def _bootstrap_stdio():
    stdio_exit_stack = AsyncExitStack()
    command_parts = shlex.split(config.mcp_stdio_server_command)
    server_params = StdioServerParameters(command=command_parts[0], args=command_parts[1:], env=None)
    read_stream, write_stream = await stdio_exit_stack.enter_async_context(stdio_client(server_params))
    session = await stdio_exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
    await session.initialize()
    return session
```

**Key advantages**:
- No network configuration required
- Simple local setup
- Direct process communication
- Lower latency for local usage

**Use cases**:
- Development and testing
- Single-user environments
- Embedded agent applications
- Offline operation

### 2. SSE Transport

Server-Sent Events (SSE) transport uses HTTP long-polling for real-time, one-way communication:

```python
# Server-side SSE setup (from server_sse.py)
async def handle_sse(request: Request) -> None:
    async with sse.connect_sse(
        request.scope,
        request.receive,
        request._send,  # noqa: SLF001
    ) as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options(),
        )
```

**Key advantages**:
- Multiple clients can connect to a single server
- Network-based communication
- Stateless server architecture
- Suitable for distributed systems

**Use cases**:
- Production deployments
- Multi-user environments
- Scalable agent infrastructure
- Cross-network operation

## Tool Interface

The MCP server defines a standardized tool interface that all tools must implement:

```python
class Tool(ABC):
    """Abstract base class for all tools."""
    name: ClassVar[str]
    description: ClassVar[str]
    input_model: ClassVar[Type[BaseToolInput]]
    output_model: ClassVar[Optional[Type[BaseModel]]] = None

    @abstractmethod
    async def execute(self, input_data: BaseToolInput) -> ToolResponse:
        """Execute the tool with given arguments."""
        pass

    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for the tool."""
        schema = {
            "name": self.name,
            "description": self.description,
            "input": self.input_model.model_json_schema(),
        }

        if self.output_model:
            schema["output"] = self.output_model.model_json_schema()

        return schema
```

The tool interface consists of:

1. **Class Variables**:
   - `name`: Tool identifier used in MCP communications
   - `description`: Human-readable tool description
   - `input_model`: Pydantic model defining input parameters
   - `output_model`: Pydantic model defining output structure (optional)

2. **Execute Method**:
   - Asynchronous method that performs the tool's functionality
   - Takes strongly-typed input data
   - Returns a structured ToolResponse

3. **Schema Method**:
   - Provides JSON Schema for tool discovery
   - Enables automatic documentation generation
   - Facilitates client-side validation

## Configuration

### Server Configuration

The server can be configured through command-line arguments:
```bash
poetry run example-mcp-server --mode=sse --host=0.0.0.0 --port=6969 --reload
```

Options:
- `--mode`: Transport mode (sse/stdio)
- `--host`: Host to bind to
- `--port`: Port to listen on
- `--reload`: Enable auto-reload for development

### Client Configuration

The client uses a configuration class:
```python
@dataclass
class MCPConfig:
    mcp_server_url: str = "http://localhost:6969"
    openai_model: str = "gpt-4o-mini"
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
```

For STDIO transport, additional options are available:
```python
@dataclass
class MCPConfig:
    openai_model: str = "gpt-4o-mini"
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    mcp_stdio_server_command: str = "poetry run example-mcp-server --mode stdio"
```

## Usage Examples

1. **Start the Server (SSE mode)**:
```bash
cd example-mcp-server
poetry run example-mcp-server --mode=sse
```

2. **Run the Client**:

Using the main launcher with transport selection:
```bash
cd example-client
poetry run python -m example_client.main --transport sse
```

Directly calling the SSE client:
```bash
cd example-client
poetry run python -m example_client.main_sse
```

Directly calling the STDIO client:
```bash
cd example-client
poetry run python -m example_client.main_stdio
```

3. **Example Queries**:
```
You: What is 2+2?
You: Calculate the square root of 144
You: Generate a random number between 1 and 100
```

## Best Practices

1. **Development**:
   - Use STDIO transport for local development
   - Enable server auto-reload during development
   - Implement proper error handling

2. **Production**:
   - Use SSE transport for production deployments
   - Configure appropriate CORS settings
   - Implement authentication if needed

3. **Tool Development**:
   - Follow the Tool interface contract
   - Provide clear input/output schemas
   - Include comprehensive documentation

## Extending the Example

To add new tools:

1. Create a new tool class implementing the Tool interface
2. Register the tool in the server's tool service
3. The client will automatically discover and use the new tool

Example tool structure:
```python
class MyNewTool(Tool):
    name = "my_new_tool"
    description = "This tool performs a custom operation"
    input_model = create_model(
        "MyNewToolInput",
        param1=(str, Field(..., description="First parameter")),
        param2=(int, Field(..., description="Second parameter")),
        __base__=BaseToolInput
    )

    async def execute(self, input_data: BaseToolInput) -> ToolResponse:
        # Access params with input_data.param1, input_data.param2
        result = f"Processed {input_data.param1} with {input_data.param2}"
        return ToolResponse.from_text(result)
```

Then register the tool in the server:
```python
def get_available_tools() -> List[Tool]:
    return [
        # ... existing tools ...
        MyNewTool(),
    ]
```
