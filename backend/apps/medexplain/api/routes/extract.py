from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...extraction.extractor import extract
from ...models.patient_data import PatientDataObject

router = APIRouter(prefix="/extract", tags=["extraction"])


class ExtractRequest(BaseModel):
    report_text: str


@router.post("", response_model=PatientDataObject)
def extract_report(body: ExtractRequest) -> PatientDataObject:
    """
    Layer 1: Read the raw compte rendu médical and return the Patient Data Object.
    If requires_doctor_review is true, the caller must go through /review before /generate.
    """
    if not body.report_text.strip():
        raise HTTPException(status_code=422, detail="report_text must not be empty")
    try:
        return extract(body.report_text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
