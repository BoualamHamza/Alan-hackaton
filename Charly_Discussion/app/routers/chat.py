"""
FastAPI router for the conversational AI assistant.
Exposes:
  POST /chat        → send a message and get a response
  DELETE /chat/{id} → clear a session's conversation history
"""

import uuid
from fastapi import APIRouter
from pydantic import BaseModel

from app.services.chat_service import chat, clear_session

router = APIRouter(prefix="/chat", tags=["Chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None  # If None, a new session is created


class ChatResponse(BaseModel):
    session_id: str
    response: str
    sources: list[str]


@router.post("", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    """
    Send a message to the AI assistant.
    If no session_id is provided, a new session is automatically created.
    Pass the returned session_id in subsequent requests to maintain conversation history.
    """
    session_id = request.session_id or str(uuid.uuid4())
    result = chat(session_id, request.message)
    return result


@router.delete("/{session_id}")
def clear_chat_session(session_id: str):
    """Clears the conversation history for a given session."""
    clear_session(session_id)
    return {"message": f"Session {session_id} cleared."}
