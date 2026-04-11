import json
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from patient_intake.config import MISTRAL_API_KEY, MISTRAL_API_URL, MISTRAL_MODEL
from patient_intake.models.database import ConversationMessage, IntakeSession, UploadedFile
from patient_intake.models.schemas import MessageResponse, SessionResponse
from patient_intake.prompts.questionnaire import QUESTIONNAIRE_SYSTEM_PROMPT


async def create_session(patient_id: str | None, db: AsyncSession) -> SessionResponse:
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    session = IntakeSession(id=session_id, patient_id=patient_id, created_at=now, status="active")
    db.add(session)
    await db.commit()
    return SessionResponse(
        session_id=session_id,
        patient_id=patient_id,
        created_at=now,
        status="active",
    )


async def process_message(session_id: str, text: str, db: AsyncSession) -> MessageResponse:
    session = await _load_session(session_id, db)

    doc_context = _build_doc_context(session.files)
    messages = _build_messages(session.messages, text, doc_context)

    mistral_data = await _call_mistral(messages)
    response_text = mistral_data.get("response", "")
    is_complete = bool(mistral_data.get("is_intake_complete", False))

    # Persist both turns
    db.add(ConversationMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="patient",
        content=text,
        created_at=datetime.now(timezone.utc),
    ))
    db.add(ConversationMessage(
        id=str(uuid.uuid4()),
        session_id=session_id,
        role="assistant",
        content=response_text,
        created_at=datetime.now(timezone.utc),
    ))
    await db.commit()

    return MessageResponse(
        session_id=session_id,
        response_text=response_text,
        is_intake_complete=is_complete,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _load_session(session_id: str, db: AsyncSession) -> IntakeSession:
    result = await db.execute(
        select(IntakeSession)
        .where(IntakeSession.id == session_id)
        .options(
            selectinload(IntakeSession.messages),
            selectinload(IntakeSession.files),
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} introuvable")
    return session


def _build_doc_context(files: list[UploadedFile]) -> str:
    if not files:
        return "Aucun document uploadé pour l'instant."
    parts = ["Documents uploadés par le patient :"]
    for f in files:
        if f.extraction_status == "done" and f.extracted_content:
            try:
                data = json.loads(f.extracted_content)
                summary = data.get("raw_summary", "Contenu extrait disponible.")
            except json.JSONDecodeError:
                summary = f.extracted_content[:400]
            parts.append(f"- {f.original_filename} ({f.file_type}) : {summary}")
        else:
            parts.append(f"- {f.original_filename} ({f.file_type}) : extraction {f.extraction_status}")
    return "\n".join(parts)


def _build_messages(history: list[ConversationMessage], new_text: str, doc_context: str) -> list[dict]:
    messages = [{"role": "system", "content": QUESTIONNAIRE_SYSTEM_PROMPT}]
    for msg in history:
        role = "user" if msg.role == "patient" else "assistant"
        messages.append({"role": role, "content": msg.content})
    messages.append({"role": "user", "content": f"{doc_context}\n\nPatient : {new_text}"})
    return messages


async def _call_mistral(messages: list[dict]) -> dict:
    if not MISTRAL_API_KEY:
        raise HTTPException(status_code=500, detail="MISTRAL_API_KEY non configurée")

    payload = {
        "model": MISTRAL_MODEL,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.4,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                MISTRAL_API_URL,
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Timeout Mistral API (questionnaire)")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Impossible de joindre Mistral API : {exc}")

    if not resp.is_success:
        raise HTTPException(status_code=502, detail=f"Erreur Mistral API {resp.status_code} : {resp.text}")

    content = resp.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"response": content, "is_intake_complete": False}
