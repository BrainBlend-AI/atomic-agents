"""Schema definitions for FastAPI Atomic Agents example."""

from typing import List, Optional

from atomic_agents import BaseIOSchema
from pydantic import Field


class ChatRequest(BaseIOSchema):
    """Request schema for chat endpoint."""

    message: str = Field(..., description="User message")
    user_id: str = Field(..., description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier for conversation continuity")


class ChatResponse(BaseIOSchema):
    """Response schema for chat endpoint."""

    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session identifier")
    suggested_questions: Optional[List[str]] = Field(
        None,
        description="Suggested initial or follow-up questions that the user could ask the assistant",
    )


class SessionCreateRequest(BaseIOSchema):
    """Request schema for creating a new session."""

    user_id: str = Field(..., description="User identifier")


class SessionCreateResponse(BaseIOSchema):
    """Response schema for session creation."""

    session_id: str = Field(..., description="Generated session identifier")
    message: str = Field(..., description="Success message")


class SessionInfo(BaseIOSchema):
    """Information about a single session."""

    session_id: str = Field(..., description="Session identifier")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class UserSessionsResponse(BaseIOSchema):
    """Response schema for listing user's sessions."""

    user_id: str = Field(..., description="User identifier")
    sessions: List[SessionInfo] = Field(..., description="List of user's sessions")


class SessionDeleteResponse(BaseIOSchema):
    """Response schema for session deletion."""

    message: str = Field(..., description="Status message")


class ConversationMessage(BaseIOSchema):
    """A single message in the conversation history."""

    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp")
    suggested_questions: Optional[List[str]] = Field(
        None, description="Suggested follow-up questions (only for assistant messages)"
    )


class ConversationHistory(BaseIOSchema):
    """Conversation history for a session."""

    session_id: str = Field(..., description="Session identifier")
    messages: List[ConversationMessage] = Field(..., description="List of messages in chronological order")
