import os
from contextlib import asynccontextmanager
from typing import Optional

import instructor
import openai
from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import SystemPromptGenerator
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import Field

load_dotenv()


class ChatRequest(BaseIOSchema):
    """Request schema for chat endpoint"""

    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session identifier for conversation continuity")


class ChatResponse(BaseIOSchema):
    """Response schema for chat endpoint"""

    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session identifier")


sessions = {}


def get_or_create_agent(session_id: str) -> AtomicAgent:
    if session_id not in sessions:
        client = instructor.from_openai(openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY")))

        system_prompt = SystemPromptGenerator(
            background=["You are a helpful AI assistant that maintains conversation context."],
            steps=["Understand the user's message", "Provide a clear and helpful response"],
            output_instructions=["Be concise and friendly", "Reference previous context when relevant"],
        )

        config = AgentConfig(
            client=client,
            model="gpt-4o-mini",
            system_prompt_generator=system_prompt,
        )

        sessions[session_id] = AtomicAgent(config=config)

    return sessions[session_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    sessions.clear()


app = FastAPI(
    title="Atomic Agents FastAPI Example",
    description="Simple example showing FastAPI integration with Atomic Agents",
    lifespan=lifespan,
)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        session_id = request.session_id or "default"
        agent = get_or_create_agent(session_id)

        result = agent.run(ChatRequest(message=request.message))
        return ChatResponse(response=result.response, session_id=session_id)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        return {"message": f"Session {session_id} cleared"}
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/sessions")
async def list_sessions():
    return {"active_sessions": list(sessions.keys())}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
