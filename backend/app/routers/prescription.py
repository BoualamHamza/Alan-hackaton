"""
FastAPI router for prescription analysis.
Exposes POST /analyze/prescription
Accepts an image (JPEG/PNG) or PDF file upload.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.prescription_service import analyze_prescription

router = APIRouter(prefix="/analyze", tags=["Prescription"])


@router.post("/prescription")
async def analyze_prescription_endpoint(file: UploadFile = File(...)):
    """
    Upload a prescription image (JPEG/PNG) or PDF.
    Returns a list of medications with plain-language explanations.
    """
    allowed_types = {"image/jpeg", "image/png", "image/jpg", "application/pdf"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Please upload a JPEG, PNG or PDF.",
        )

    file_bytes = await file.read()

    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 10MB.",
        )

    result = analyze_prescription(file_bytes, file.filename)
    return result
