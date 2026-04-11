import base64
import json
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from patient_intake.config import (
    ALLOWED_MIME_TYPES,
    MISTRAL_API_KEY,
    MISTRAL_API_URL,
    MISTRAL_MODEL,
    MAX_FILE_SIZE_BYTES,
)
from patient_intake.models.database import IntakeSession, UploadedFile, async_session_factory
from patient_intake.models.schemas import UploadedFileInfo, UploadResponse
from patient_intake.prompts.document_extraction import DOCUMENT_EXTRACTION_SYSTEM_PROMPT
from patient_intake.storage.file_storage import FileStorage


async def upload_files(
    session_id: str,
    files: list[UploadFile],
    db: AsyncSession,
    storage: FileStorage,
) -> UploadResponse:
    result = await db.execute(select(IntakeSession).where(IntakeSession.id == session_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Session {session_id!r} introuvable")

    uploaded: list[UploadedFileInfo] = []

    for file in files:
        content_type = file.content_type or ""
        if content_type == "image/jpg":
            content_type = "image/jpeg"

        if content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=415,
                detail=f"Format non supporté : '{content_type}'. Acceptés : JPG, PNG, PDF.",
            )

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail=f"Fichier vide : {file.filename}")
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"Fichier trop volumineux : {file.filename} (max 20 MB)",
            )

        storage_path = await storage.save(session_id, file.filename or "upload", content)
        file_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        db.add(UploadedFile(
            id=file_id,
            session_id=session_id,
            original_filename=file.filename or "upload",
            file_type=content_type,
            storage_path=storage_path,
            upload_date=now,
            extraction_status="pending",
        ))

        uploaded.append(UploadedFileInfo(
            file_id=file_id,
            original_filename=file.filename or "upload",
            file_type=content_type,
            upload_date=now,
            extraction_status="pending",
        ))

    await db.commit()
    return UploadResponse(session_id=session_id, uploaded_files=uploaded)


async def extract_file_content(file_id: str, storage: FileStorage) -> None:
    """Background task — creates its own DB session."""
    async with async_session_factory() as db:
        result = await db.execute(select(UploadedFile).where(UploadedFile.id == file_id))
        db_file = result.scalar_one_or_none()
        if not db_file:
            return

        db_file.extraction_status = "processing"
        await db.commit()

        try:
            file_bytes = await storage.load(db_file.storage_path)
            extracted = await _call_mistral_extraction(file_bytes, db_file.file_type)
            db_file.extracted_content = json.dumps(extracted, ensure_ascii=False)
            db_file.extraction_status = "done"
        except Exception:
            db_file.extraction_status = "failed"
        finally:
            await db.commit()


# ---------------------------------------------------------------------------
# Mistral vision call
# ---------------------------------------------------------------------------

async def _call_mistral_extraction(file_bytes: bytes, mime_type: str) -> dict:
    if not MISTRAL_API_KEY:
        raise RuntimeError("MISTRAL_API_KEY non configurée")

    b64 = base64.standard_b64encode(file_bytes).decode()

    if mime_type == "application/pdf":
        file_block: dict = {
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{b64}",
        }
    else:
        file_block = {
            "type": "image_url",
            "image_url": f"data:{mime_type};base64,{b64}",
        }

    payload = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": DOCUMENT_EXTRACTION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Analyse ce document médical et extrais toutes les informations pertinentes.",
                    },
                    file_block,
                ],
            },
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            MISTRAL_API_URL,
            headers={
                "Authorization": f"Bearer {MISTRAL_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if not resp.is_success:
        raise RuntimeError(f"Mistral API error {resp.status_code} : {resp.text[:200]}")

    content = resp.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {"raw_summary": content, "error": "json_parse_failed"}
