"""FastAPI application for conversational AI with session management."""

import json
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict

from atomic_agents import AtomicAgent
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from fastapi_memory.lib.agents.chat_agent import create_async_chat_agent, create_chat_agent
from fastapi_memory.lib.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationHistory,
    ConversationMessage,
    SessionCreateResponse,
    SessionDeleteResponse,
    SessionInfo,
    UserSessionsResponse,
)

# Session storage: user_id -> session_id -> agent
sessions: Dict[str, Dict[str, AtomicAgent[ChatRequest, ChatResponse]]] = {}
async_sessions: Dict[str, Dict[str, AtomicAgent[ChatRequest, ChatResponse]]] = {}

# Session metadata: user_id -> session_id -> creation_timestamp
session_metadata: Dict[str, Dict[str, str]] = {}

# Conversation history: user_id -> session_id -> list of messages
conversation_history: Dict[str, Dict[str, list]] = {}


def _generate_session_id() -> str:
    """Generate a unique session identifier.

    Returns:
        UUID-based session identifier
    """
    return str(uuid.uuid4())


def _ensure_user_exists(user_id: str) -> None:
    """Ensure user exists in all storage dictionaries.

    Args:
        user_id: User identifier
    """
    if user_id not in sessions:
        sessions[user_id] = {}
    if user_id not in async_sessions:
        async_sessions[user_id] = {}
    if user_id not in session_metadata:
        session_metadata[user_id] = {}
    if user_id not in conversation_history:
        conversation_history[user_id] = {}


def _ensure_session_history_exists(user_id: str, session_id: str) -> None:
    """Ensure conversation history exists for a session.

    Args:
        user_id: User identifier
        session_id: Session identifier
    """
    _ensure_user_exists(user_id)
    if session_id not in conversation_history[user_id]:
        conversation_history[user_id][session_id] = []


def _add_message_to_history(
    user_id: str,
    session_id: str,
    role: str,
    content: str,
    suggested_questions: list[str] = None,
) -> None:
    """Add a message to the conversation history.

    Args:
        user_id: User identifier
        session_id: Session identifier
        role: Message role (user or assistant)
        content: Message content
        suggested_questions: Optional list of suggested questions
    """
    _ensure_session_history_exists(user_id, session_id)
    message = {
        "role": role,
        "content": content,
        "timestamp": datetime.now().isoformat(),
        "suggested_questions": suggested_questions,
    }
    conversation_history[user_id][session_id].append(message)


def get_or_create_agent(user_id: str, session_id: str) -> AtomicAgent[ChatRequest, ChatResponse]:
    """Get existing agent or create new synchronous agent for the session.

    Args:
        user_id: User identifier
        session_id: Session identifier

    Returns:
        AtomicAgent configured for synchronous chat operations
    """
    _ensure_user_exists(user_id)
    if session_id not in sessions[user_id]:
        sessions[user_id][session_id] = create_chat_agent()
        if session_id not in session_metadata[user_id]:
            session_metadata[user_id][session_id] = datetime.now().isoformat()
    return sessions[user_id][session_id]


def get_or_create_async_agent(user_id: str, session_id: str) -> AtomicAgent[ChatRequest, ChatResponse]:
    """Get existing agent or create new asynchronous agent for the session.

    Args:
        user_id: User identifier
        session_id: Session identifier

    Returns:
        AtomicAgent configured for asynchronous streaming operations
    """
    _ensure_user_exists(user_id)
    if session_id not in async_sessions[user_id]:
        async_sessions[user_id][session_id] = create_async_chat_agent()
        if session_id not in session_metadata[user_id]:
            session_metadata[user_id][session_id] = datetime.now().isoformat()
    return async_sessions[user_id][session_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to clean up resources on shutdown.

    Args:
        app: FastAPI application instance

    Yields:
        None
    """
    yield
    sessions.clear()
    async_sessions.clear()
    session_metadata.clear()
    conversation_history.clear()


app = FastAPI(
    title="Atomic Agents FastAPI Example",
    description="Simple example showing FastAPI integration with Atomic Agents",
    version="1.0.0",
    lifespan=lifespan,
)


@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message using non-streaming response.

    Args:
        request: Chat request containing message, user_id, and optional session ID

    Returns:
        ChatResponse with agent's reply and suggested questions

    Raises:
        HTTPException: If message processing fails
    """
    try:
        if not request.session_id:
            raise HTTPException(
                status_code=400, detail="session_id is required. Create a session first using POST /users/{user_id}/sessions"
            )

        # Store user message in history
        _add_message_to_history(request.user_id, request.session_id, "user", request.message)

        agent = get_or_create_agent(request.user_id, request.session_id)

        result = agent.run(ChatRequest(message=request.message, user_id=request.user_id))

        # Store assistant response in history
        _add_message_to_history(
            request.user_id,
            request.session_id,
            "assistant",
            result.response,
            getattr(result, "suggested_questions", None),
        )

        return ChatResponse(
            response=result.response,
            session_id=request.session_id,
            suggested_questions=getattr(result, "suggested_questions", None),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process message: {str(e)}")


@app.post("/chat/stream", tags=["Chat"])
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Process a chat message using streaming response.

    Args:
        request: Chat request containing message, user_id, and optional session ID

    Returns:
        StreamingResponse with Server-Sent Events format

    Raises:
        HTTPException: If streaming setup fails
    """
    try:
        if not request.session_id:
            raise HTTPException(
                status_code=400, detail="session_id is required. Create a session first using POST /users/{user_id}/sessions"
            )

        # Store user message in history
        _add_message_to_history(request.user_id, request.session_id, "user", request.message)

        agent = get_or_create_async_agent(request.user_id, request.session_id)

        async def generate():
            """Generate Server-Sent Events stream."""
            full_response = ""
            final_suggested_questions = []
            try:
                async for chunk in agent.run_async_stream(ChatRequest(message=request.message, user_id=request.user_id)):
                    chunk_dict = chunk.model_dump() if hasattr(chunk, "model_dump") else {}
                    response_text = chunk_dict.get("response", "")
                    full_response = response_text  # Keep updating with latest full text

                    if chunk_dict.get("suggested_questions"):
                        final_suggested_questions = chunk_dict.get("suggested_questions")

                    data = {
                        "response": response_text,
                        "session_id": request.session_id,
                        "suggested_questions": chunk_dict.get("suggested_questions"),
                    }
                    yield f"data: {json.dumps(data)}\n\n"

                # Store complete assistant response in history
                if full_response:
                    _add_message_to_history(
                        request.user_id,
                        request.session_id,
                        "assistant",
                        full_response,
                        final_suggested_questions,
                    )

            except Exception as e:
                error_data = {
                    "error": str(e),
                    "session_id": request.session_id,
                }
                yield f"data: {json.dumps(error_data)}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to setup stream: {str(e)}")


@app.post("/users/{user_id}/sessions", response_model=SessionCreateResponse, tags=["Sessions"])
async def create_session(user_id: str) -> SessionCreateResponse:
    """Create a new chat session for a user.

    Args:
        user_id: User identifier

    Returns:
        SessionCreateResponse with generated session ID

    Raises:
        HTTPException: If session creation fails
    """
    try:
        _ensure_user_exists(user_id)
        session_id = _generate_session_id()
        session_metadata[user_id][session_id] = datetime.now().isoformat()

        return SessionCreateResponse(session_id=session_id, message=f"Session '{session_id}' created successfully")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.get("/users/{user_id}/sessions", response_model=UserSessionsResponse, tags=["Sessions"])
async def get_user_sessions(user_id: str) -> UserSessionsResponse:
    """Get all sessions for a specific user.

    Args:
        user_id: User identifier

    Returns:
        UserSessionsResponse with list of user's sessions
    """
    _ensure_user_exists(user_id)

    # Collect all unique session IDs for this user from both dicts
    sync_sessions = set(sessions.get(user_id, {}).keys())
    async_session_ids = set(async_sessions.get(user_id, {}).keys())
    all_session_ids = sync_sessions | async_session_ids

    # Build session info list
    session_list = [
        SessionInfo(session_id=sid, created_at=session_metadata.get(user_id, {}).get(sid)) for sid in sorted(all_session_ids)
    ]

    return UserSessionsResponse(user_id=user_id, sessions=session_list)


@app.get("/users/{user_id}/sessions/{session_id}/history", response_model=ConversationHistory, tags=["Sessions"])
async def get_conversation_history(user_id: str, session_id: str) -> ConversationHistory:
    """Get conversation history for a specific session.

    Args:
        user_id: User identifier
        session_id: Session identifier

    Returns:
        ConversationHistory with all messages in the session

    Raises:
        HTTPException: If session is not found
    """
    _ensure_session_history_exists(user_id, session_id)

    messages = conversation_history.get(user_id, {}).get(session_id, [])

    return ConversationHistory(session_id=session_id, messages=[ConversationMessage(**msg) for msg in messages])


@app.delete("/users/{user_id}/sessions/{session_id}", response_model=SessionDeleteResponse, tags=["Sessions"])
async def delete_session(user_id: str, session_id: str) -> SessionDeleteResponse:
    """Delete a specific session for a user.

    Args:
        user_id: User identifier
        session_id: Session identifier to delete

    Returns:
        SessionDeleteResponse with success message

    Raises:
        HTTPException: If session is not found
    """
    found = False

    if user_id in sessions and session_id in sessions[user_id]:
        del sessions[user_id][session_id]
        found = True

    if user_id in async_sessions and session_id in async_sessions[user_id]:
        del async_sessions[user_id][session_id]
        found = True

    if user_id in session_metadata and session_id in session_metadata[user_id]:
        del session_metadata[user_id][session_id]

    if user_id in conversation_history and session_id in conversation_history[user_id]:
        del conversation_history[user_id][session_id]

    if not found:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found for user '{user_id}'")

    return SessionDeleteResponse(message=f"Session '{session_id}' deleted successfully")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
