"""
Cases API — orchestrates the full pipeline from patient form data to generated videos.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException, UploadFile, File
from fastapi.responses import FileResponse

from ...config import settings
from ...extraction.extractor import extract
from ...script.generator import generate_script
from ...pipeline.orchestrator import run_pipeline
from ...synthesis.document_extractor import extract_documents
from ...synthesis.report_synthesizer import synthesize_report

router = APIRouter()

# In-memory store: case_id → case dict
cases_store: dict[str, dict[str, Any]] = {}


# ── helpers ──────────────────────────────────────────────────────────────────

def _public_case(case: dict[str, Any]) -> dict[str, Any]:
    """Return case dict without internal filesystem paths."""
    return {k: v for k, v in case.items() if not k.startswith("_")}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── background pipeline ───────────────────────────────────────────────────────

async def _run_generation_pipeline(
    case_id: str,
    form_data: dict[str, Any],
    file_tuples: list[tuple[str, bytes, str]],
) -> None:
    """Full synthesis → extraction → generation pipeline, runs in background."""
    cases_store[case_id]["videoStatus"] = "processing"
    cases_store[case_id]["updatedAt"] = _now_iso()

    try:
        # Step 1 — extract text from uploaded documents
        doc_text = await extract_documents(file_tuples)

        # Step 2 — synthesize a formal medical report from patient input
        report_text = synthesize_report(
            title=form_data["title"],
            specialty=form_data["specialty"],
            doctor_name=form_data["doctorName"],
            visit_date=form_data["visitDate"],
            symptoms=form_data["symptoms"],
            summary=form_data["summary"],
            document_content=doc_text,
        )

        # Step 3 — extract PatientDataObject from the report
        pdo = extract(report_text)

        # Step 4 — force auto-approve (bypass the doctor-review gate)
        pdo.doctor_approved = True
        pdo.approved_at = _now_iso()
        pdo.extraction_metadata.requires_doctor_review = False

        # Step 5 — generate narration scripts for both videos
        loop = asyncio.get_event_loop()
        _, script_v1 = await loop.run_in_executor(None, generate_script, pdo, 1)
        _, script_v2 = await loop.run_in_executor(None, generate_script, pdo, 2)

        # Step 6 — run the full video pipeline (async, both videos concurrent)
        # Use a per-case subdirectory so concurrent/sequential cases never overwrite each other
        case_output_dir = os.path.join(settings.output_dir, case_id)
        os.makedirs(case_output_dir, exist_ok=True)
        video_1_path, video_2_path = await run_pipeline(
            pdo=pdo,
            video_1_script=script_v1,
            video_2_script=script_v2,
            output_dir=case_output_dir,
        )

        # Step 7 — update store with results
        cases_store[case_id].update(
            {
                "videoStatus": "ready",
                "videos": [
                    {
                        "id": "video_1",
                        "title": "Understanding Your Condition",
                        "url": f"/cases/{case_id}/videos/1",
                    },
                    {
                        "id": "video_2",
                        "title": "Your Treatment Plan",
                        "url": f"/cases/{case_id}/videos/2",
                    },
                ],
                "_video_1_path": video_1_path,
                "_video_2_path": video_2_path,
                "errorMessage": None,
                "updatedAt": _now_iso(),
            }
        )

    except Exception as exc:  # noqa: BLE001
        cases_store[case_id].update(
            {
                "videoStatus": "error",
                "errorMessage": str(exc),
                "updatedAt": _now_iso(),
            }
        )
        raise


# ── endpoints ─────────────────────────────────────────────────────────────────

@router.post("", status_code=201)
async def create_case(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    specialty: str = Form(...),
    doctorName: str = Form(...),
    visitDate: str = Form(...),
    summary: str = Form(""),
    symptoms: str = Form(""),
    hasVoiceNote: str = Form("false"),
    documents: list[UploadFile] = File(default=[]),
    voiceNote: UploadFile | None = File(default=None),
) -> dict[str, Any]:
    # Read all file bytes eagerly — UploadFile objects expire after the request
    file_tuples: list[tuple[str, bytes, str]] = []
    for f in documents:
        content = await f.read()
        file_tuples.append((f.filename or "document", content, f.content_type or "application/octet-stream"))

    symptoms_list = [s.strip() for s in symptoms.split(",") if s.strip()]

    case_id = str(uuid.uuid4())
    now = _now_iso()

    case: dict[str, Any] = {
        "id": case_id,
        "title": title,
        "specialty": specialty,
        "doctorName": doctorName,
        "visitDate": visitDate,
        "summary": summary,
        "symptoms": symptoms_list,
        "createdAt": now,
        "updatedAt": now,
        "documentsCount": len(documents),
        "hasVoiceNote": hasVoiceNote.lower() == "true",
        "videoStatus": "pending",
        "videos": None,
        "errorMessage": None,
        # internal — not exposed to client
        "_video_1_path": None,
        "_video_2_path": None,
    }
    cases_store[case_id] = case

    form_data = {
        "title": title,
        "specialty": specialty,
        "doctorName": doctorName,
        "visitDate": visitDate,
        "summary": summary,
        "symptoms": symptoms_list,
    }

    background_tasks.add_task(_run_generation_pipeline, case_id, form_data, file_tuples)

    return _public_case(case)


@router.get("/{case_id}")
def get_case(case_id: str) -> dict[str, Any]:
    if case_id not in cases_store:
        raise HTTPException(status_code=404, detail="Case not found")
    return _public_case(cases_store[case_id])


@router.get("/{case_id}/videos/{video_number}")
def get_video(case_id: str, video_number: int) -> FileResponse:
    if case_id not in cases_store:
        raise HTTPException(status_code=404, detail="Case not found")

    case = cases_store[case_id]

    if case["videoStatus"] != "ready":
        raise HTTPException(status_code=425, detail="Videos are not ready yet")

    if video_number not in (1, 2):
        raise HTTPException(status_code=400, detail="video_number must be 1 or 2")

    video_path = case.get(f"_video_{video_number}_path")
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(status_code=500, detail="Video file not found on disk")

    return FileResponse(
        path=video_path,
        media_type="video/mp4",
        headers={
            "Content-Disposition": "inline",
            "Accept-Ranges": "bytes",
            "Cache-Control": "no-cache",
        },
    )
