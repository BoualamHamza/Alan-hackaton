"""
Conversational AI assistant for patients.
- Maintains conversation history per session (stored in memory)
- Retrieves relevant MedlinePlus context for each question (RAG)
- Uses Mistral Large to generate patient-friendly responses
"""

import time
from mistralai.client import Mistral
from ..core.config import settings
from ..services.vector_store import retrieve


def call_with_retry(fn, *args, **kwargs):
    for attempt in range(8):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            if "429" in str(e) or "rate_limited" in str(e):
                wait = 30 * (attempt + 1)
                print(f"Rate limit hit, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Mistral API rate limit — max retries exceeded.")

client = Mistral(api_key=settings.mistral_api_key)
MISTRAL_MODEL = "mistral-large-latest"

# In-memory session store: {session_id: [{"role": ..., "content": ...}]}
# For the demo this is sufficient — in production this would be a database
sessions: dict[str, list[dict]] = {}

SYSTEM_PROMPT = """You are MedBridge, a compassionate AI medical assistant helping patients understand their health.

Your role:
- Explain medical information in simple, clear language that anyone can understand
- Help patients understand their prescriptions, conditions, and medical results
- Answer questions based on the medical reference information provided to you
- Be warm, reassuring, and empathetic

Your strict limits:
- Never make a diagnosis
- Never recommend changing a prescribed dose
- Always remind patients to consult their doctor for medical decisions
- If a question is outside your knowledge, say so honestly

Respond in the same language the patient uses."""


def get_or_create_session(session_id: str) -> list[dict]:
    """Returns existing session history or creates a new one."""
    if session_id not in sessions:
        sessions[session_id] = []
    return sessions[session_id]


def clear_session(session_id: str) -> None:
    """Clears the conversation history for a session."""
    sessions.pop(session_id, None)


def chat(session_id: str, user_message: str) -> dict:
    """
    Main chat function.
    1. Retrieves relevant MedlinePlus context for the question
    2. Builds the message history with context injected
    3. Calls Mistral Large and returns the response
    """
    history = get_or_create_session(session_id)

    # Retrieve relevant medical context from ChromaDB
    context_chunks = retrieve(user_message, k=4)
    context_text = "\n\n".join(c["text"] for c in context_chunks)
    sources = list({c["title"] for c in context_chunks})

    # Build the system message with injected context
    system_with_context = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Relevant medical reference information for this question:\n{context_text}"
    )

    # Add user message to history
    history.append({"role": "user", "content": user_message})

    # Build full message list for the API call
    messages = [{"role": "system", "content": system_with_context}] + history

    response = call_with_retry(
        client.chat.complete,
        model=MISTRAL_MODEL,
        messages=messages,
    )

    assistant_message = response.choices[0].message.content.strip()

    # Save assistant response to history
    history.append({"role": "assistant", "content": assistant_message})

    return {
        "session_id": session_id,
        "response": assistant_message,
        "sources": sources,
    }
