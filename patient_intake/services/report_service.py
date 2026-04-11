import json
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from patient_intake.config import MISTRAL_API_KEY, MISTRAL_API_URL, MISTRAL_MODEL
from patient_intake.models.database import IntakeSession, MedicalReportDB, UploadedFile
from patient_intake.models.schemas import MedicalReport
from patient_intake.prompts.report_generation import REPORT_GENERATION_SYSTEM_PROMPT
from patient_intake.services.reminder_service import build_reminders


async def generate_report(session_id: str, db: AsyncSession) -> MedicalReport:
    session = await _load_session(session_id, db)

    context = _build_context(session)
    now = datetime.now(timezone.utc).isoformat()

    report_dict = await _call_mistral_report(context, session.patient_id, now)

    # System fills uploaded_documents
    report_dict["uploaded_documents"] = _build_uploaded_docs(session.files)

    # Enrich metadata
    data_sources: list[str] = []
    if session.messages:
        data_sources.append("patient_input")
    if session.files:
        data_sources.append("uploaded_documents")
    report_dict.setdefault("metadata", {})
    report_dict["metadata"]["data_sources"] = data_sources

    completeness, missing = _compute_completeness(report_dict)
    report_dict["metadata"]["completeness_score"] = completeness
    report_dict["metadata"]["missing_info"] = missing

    # Generate reminders from all medications found in documents + conversation
    all_medications = _collect_all_medications(report_dict, session.files)
    report_dict["reminders"] = build_reminders(all_medications)

    try:
        report = MedicalReport(**report_dict)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Validation du rapport échouée : {exc}")

    # Upsert
    existing = await db.execute(
        select(MedicalReportDB).where(MedicalReportDB.session_id == session_id)
    )
    db_report = existing.scalar_one_or_none()
    if db_report:
        db_report.report_json = report.model_dump_json()
        db_report.generated_at = datetime.now(timezone.utc)
    else:
        db.add(MedicalReportDB(
            session_id=session_id,
            report_json=report.model_dump_json(),
        ))

    session.status = "completed"
    await db.commit()

    return report


async def get_report(session_id: str, db: AsyncSession) -> MedicalReport:
    result = await db.execute(
        select(MedicalReportDB).where(MedicalReportDB.session_id == session_id)
    )
    db_report = result.scalar_one_or_none()
    if not db_report:
        raise HTTPException(
            status_code=404,
            detail=f"Aucun rapport pour la session {session_id!r}. Appelez d'abord POST /generate-report.",
        )
    return MedicalReport.model_validate_json(db_report.report_json)


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


def _collect_all_medications(report_dict: dict, files: list[UploadedFile]) -> list[dict]:
    """
    Collecte tous les médicaments trouvés :
    1. Dans le rapport généré par Mistral (treatments.current_medications)
    2. Dans les documents uploadés extraits (prescriptions)
    Déduplique par nom de médicament.
    """
    seen: set[str] = set()
    medications: list[dict] = []

    # From report
    for med in (report_dict.get("treatments") or {}).get("current_medications") or []:
        name = (med.get("name") or "").lower().strip()
        if name and name not in seen:
            seen.add(name)
            medications.append(med)

    # From extracted documents (prescriptions)
    for f in files:
        if f.extraction_status != "done" or not f.extracted_content:
            continue
        try:
            data = json.loads(f.extracted_content)
        except json.JSONDecodeError:
            continue
        for med in data.get("medications") or []:
            name = (med.get("name") or "").lower().strip()
            if name and name not in seen:
                seen.add(name)
                medications.append(med)

    return medications


def _build_context(session: IntakeSession) -> str:
    parts = [f"=== SESSION {session.id} ==="]

    if session.messages:
        parts.append("\n--- CONVERSATION PATIENT ---")
        for msg in session.messages:
            label = "Patient" if msg.role == "patient" else "Assistant"
            parts.append(f"{label} : {msg.content}")

    if session.files:
        parts.append("\n--- DOCUMENTS MÉDICAUX UPLOADÉS ---")
        for f in session.files:
            parts.append(f"\nFichier : {f.original_filename} ({f.file_type}) — extraction : {f.extraction_status}")
            if f.extraction_status == "done" and f.extracted_content:
                try:
                    data = json.loads(f.extracted_content)
                    parts.append(f"Contenu extrait :\n{json.dumps(data, ensure_ascii=False, indent=2)}")
                except json.JSONDecodeError:
                    parts.append(f"Contenu extrait : {f.extracted_content[:2000]}")

    return "\n".join(parts)


def _build_uploaded_docs(files: list[UploadedFile]) -> list[dict]:
    docs = []
    for f in files:
        summary = None
        if f.extracted_content:
            try:
                data = json.loads(f.extracted_content)
                summary = data.get("raw_summary")
            except json.JSONDecodeError:
                summary = f.extracted_content[:200]
        docs.append({
            "file_id": f.id,
            "original_filename": f.original_filename,
            "file_type": f.file_type,
            "upload_date": f.upload_date.isoformat(),
            "extracted_content_summary": summary,
            "storage_path": f.storage_path,
        })
    return docs


async def _call_mistral_report(context: str, patient_id: str | None, generated_at: str) -> dict:
    if not MISTRAL_API_KEY:
        raise HTTPException(status_code=500, detail="MISTRAL_API_KEY non configurée")

    user_content = (
        f"Génère le compte rendu médical structuré.\n"
        f"patient_id : {patient_id or 'unknown'}\n"
        f"generated_at : {generated_at}\n\n"
        f"{context}"
    )

    payload = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": REPORT_GENERATION_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 4096,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
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
            raise HTTPException(status_code=504, detail="Timeout Mistral API (génération rapport)")
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Impossible de joindre Mistral API : {exc}")

    if not resp.is_success:
        raise HTTPException(status_code=502, detail=f"Erreur Mistral API {resp.status_code} : {resp.text}")

    content = resp.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Impossible de parser le JSON du rapport Mistral : {exc}")


def _compute_completeness(report: dict) -> tuple[float, list[str]]:
    score = 0.0
    missing: list[str] = []

    profile = report.get("patient_profile") or {}
    filled = sum(1 for k in ("age", "sex") if profile.get(k))
    if filled == 2:
        score += 0.20
    elif filled == 1:
        score += 0.10
        missing.append("patient_profile : age ou sex manquant")
    else:
        missing.append("patient_profile : age et sex inconnus")

    condition = report.get("current_condition") or {}
    if condition.get("primary_diagnosis") or condition.get("description_summary"):
        score += 0.15
    else:
        missing.append("current_condition : diagnostic / description principale manquant")
    if condition.get("symptoms"):
        score += 0.15
    else:
        missing.append("current_condition : symptômes non renseignés")

    treatments = report.get("treatments") or {}
    if treatments.get("current_medications"):
        score += 0.25
    else:
        missing.append("treatments : aucun médicament actuel renseigné")

    if report.get("lab_results") or report.get("imaging"):
        score += 0.15
    else:
        missing.append("lab_results / imaging : aucun résultat biologique ou imagerie")

    lifestyle = report.get("lifestyle_context") or {}
    if any(lifestyle.get(k) for k in ("activity_level", "diet_notes", "sleep_notes", "stress_level")):
        score += 0.10
    else:
        missing.append("lifestyle_context : informations de mode de vie manquantes")

    return round(score, 2), missing
