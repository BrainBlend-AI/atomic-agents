# FastAPI with Atomic Agents

A comprehensive example demonstrating how to integrate Atomic Agents with FastAPI for building multi-user, multi-session conversational APIs.

## Features

- **Multi-user support**: Each user can have multiple independent chat sessions
- **Conversation history**: Full conversation history is stored and restored when you return to a session
- **User ID persistence**: Client automatically generates and stores a persistent user ID
- **Auto-generated session IDs**: Sessions are created with UUIDs - no manual IDs needed
- **Session management**: View, create, and delete sessions per user
- **RESTful API**: Clean endpoints for chat and session management
- **Interactive CLI client**: Rich terminal interface with session selection
- **Streaming support**: Both standard and streaming chat responses
- **Type safety**: Pydantic schemas for request/response validation

## Setup

1. Install dependencies:
```bash
uv sync
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

### Option 1: Interactive Client (Recommended)

Start the server:
```bash
uv run python fastapi_memory/main.py
```

In a separate terminal, run the interactive client:
```bash
uv run python fastapi_memory/client.py
```

The client will:
1. Auto-generate and persist a user ID (stored in `~/.fastapi_memory_user_id`)
2. Show your existing chat sessions or prompt you to create one
3. Load full conversation history when you select an existing session
4. Let you chat in streaming or non-streaming mode (type `/exit` to go back)
5. Manage your sessions (view/delete)

### Option 2: Direct API Usage

Start the FastAPI server:
```bash
uv run python fastapi_memory/main.py
```

The API will be available at `http://localhost:8000`.

## API Documentation

Once running, visit:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## API Usage Examples

### 1. Create a new session for a user:
```bash
curl -X POST "http://localhost:8000/users/user123/sessions"
```
Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Session created successfully"
}
```

### 2. Get all sessions for a user:
```bash
curl "http://localhost:8000/users/user123/sessions"
```
Response:
```json
{
  "user_id": "user123",
  "sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2025-01-23T10:30:00"
    }
  ]
}
```

### 3. Send a chat message:
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, how are you?",
    "user_id": "user123",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### 4. Get conversation history for a session:
```bash
curl "http://localhost:8000/users/user123/sessions/550e8400-e29b-41d4-a716-446655440000/history"
```
Response:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "messages": [
    {
      "role": "user",
      "content": "Hello, how are you?",
      "timestamp": "2025-01-23T10:31:00"
    },
    {
      "role": "assistant",
      "content": "I'm doing well, thank you for asking!",
      "timestamp": "2025-01-23T10:31:02",
      "suggested_questions": [
        "What can you do?",
        "Tell me a joke",
        "How does this work?"
      ]
    }
  ]
}
```

### 5. Delete a session:
```bash
curl -X DELETE "http://localhost:8000/users/user123/sessions/550e8400-e29b-41d4-a716-446655440000"
```

### 6. Test the API:
```bash
uv run python test_api.py
```

## How It Works

The example demonstrates several key architectural patterns:

### Server Architecture

1. **Multi-User Session Management**:
   - Data structure: `user_id → session_id → agent_instance`
   - Each user can have unlimited independent chat sessions
   - Sessions are isolated - no data leakage between users or sessions

2. **Conversation History Storage**:
   - All messages are stored with timestamps
   - Separate storage: `user_id → session_id → messages[]`
   - History persists across client reconnections
   - Automatically loaded when resuming a session

3. **Auto-Generated Session IDs**:
   - Server generates UUIDs for new sessions
   - Eliminates user input errors and collisions
   - Tracked with creation timestamps

4. **Lazy Initialization**:
   - Agent instances created on-demand when first accessed
   - Reduces memory footprint for inactive sessions
   - Conversation history maintained independently

5. **Proper Lifecycle Management**:
   - Lifespan context manager ensures cleanup on shutdown
   - Memory released when sessions are deleted
   - History cleared along with session deletion

6. **Type Safety**:
   - Pydantic schemas validate all requests/responses
   - Clear API contracts with automatic documentation

### Client Architecture

1. **User ID Persistence**:
   - Client generates a UUID on first run
   - Stored in `~/.fastapi_memory_user_id`
   - Reused across sessions for continuity

2. **Session Discovery**:
   - Fetches user's sessions from server on startup
   - Displays sessions with creation timestamps
   - Allows selection or creation of new sessions

3. **Conversation History Loading**:
   - Automatically fetches history when loading a session
   - Displays full conversation context before continuing
   - Seamlessly resume conversations from where you left off

4. **Rich Terminal UI**:
   - Interactive menus with Rich library
   - Streaming and non-streaming chat modes
   - Session management interface
   - Type `/exit` to return to menu (not Escape)

## Project Structure

```
fastapi-memory/
├── pyproject.toml              # Project dependencies
├── .env.example                # Environment variable template
├── README.md                   # This file
├── test_api.py                 # API testing script
└── fastapi_memory/
    ├── __init__.py
    ├── main.py                 # FastAPI server
    ├── client.py               # Interactive CLI client
    └── lib/
        ├── agents/
        │   └── chat_agent.py   # Agent configuration
        ├── config.py           # Configuration constants
        └── schemas.py          # Pydantic schemas
```

## Related Examples

For more advanced usage, check out:
- `mcp-agent/example-client/example_client/main_fastapi.py` - Advanced example with MCP protocol integration
