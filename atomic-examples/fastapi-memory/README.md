# FastAPI with Atomic Agents

A simple example demonstrating how to integrate Atomic Agents with FastAPI for building stateful conversational APIs.

## Features

- Session-based conversation management
- RESTful API endpoints for chat interactions
- Automatic session creation and cleanup
- Environment-based configuration

## Setup

1. Install dependencies:
```bash
poetry install
```

2. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

Or create a `.env` file in the project root:
```
OPENAI_API_KEY=your_openai_api_key
```

## Running the Example

Start the FastAPI server:
```bash
poetry run python fastapi_memory/main.py
```

The API will be available at `http://localhost:8000`.

## API Documentation

Once running, visit:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## Usage Examples

### Send a message (creates new session automatically):
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, what can you help me with?"}'
```

### Continue a conversation with session ID:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me more about that", "session_id": "user123"}'
```

### List active sessions:
```bash
curl "http://localhost:8000/sessions"
```

### Clear a specific session:
```bash
curl -X DELETE "http://localhost:8000/sessions/user123"
```

## How It Works

The example demonstrates several key patterns:

1. **Session Management**: Each session maintains its own agent instance with independent conversation history.

2. **Lazy Initialization**: Agent instances are created on-demand when a session is first accessed.

3. **Automatic Cleanup**: The lifespan context manager ensures proper cleanup when the application shuts down.

4. **Type Safety**: Uses Pydantic schemas for request/response validation.

## Project Structure

```
fastapi-memory/
├── pyproject.toml          # Project dependencies
├── .env.example            # Environment variable template
├── README.md               # This file
└── fastapi_memory/
    └── main.py             # FastAPI application
```

## Related Examples

For more advanced usage, check out:
- `mcp-agent/example-client/example_client/main_fastapi.py` - Advanced example with MCP protocol integration
