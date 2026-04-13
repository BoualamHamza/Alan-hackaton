from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...models.patient_data import PatientDataObject, PDOValidationError
from ...review.reviewer import approve

router = APIRouter(prefix="/review", tags=["review"])


class ApproveRequest(BaseModel):
    pdo: PatientDataObject


class CorrectRequest(BaseModel):
    pdo: PatientDataObject
    corrections: Dict[str, Any]


@router.post("/approve", response_model=PatientDataObject)
def approve_pdo(body: ApproveRequest) -> PatientDataObject:
    """
    Layer 2: Doctor approves the extracted PDO without corrections.
    Returns the approved PDO (doctor_approved=True).
    """
    try:
        return approve(body.pdo)
    except PDOValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/correct", response_model=PatientDataObject)
def correct_and_approve(body: CorrectRequest) -> PatientDataObject:
    """
    Layer 2: Doctor applies corrections and approves.
    corrections is a flat dict of dot-notation paths to new values.
    Example: {"video_1_disease.severity.level": "moderate"}
    """
    try:
        return approve(body.pdo, corrections=body.corrections)
    except PDOValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=422, detail=f"Invalid correction path: {exc}"
        ) from exc
