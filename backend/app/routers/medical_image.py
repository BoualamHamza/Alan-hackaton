"""
FastAPI router for medical image analysis.
Exposes POST /analyze/image
Accepts an image (JPEG/PNG) or PDF file upload.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException

from app.services.medical_image_service import analyze_medical_image

router = APIRouter(prefix="/analyze", tags=["Medical Image"])


@router.post("/image")
async def analyze_image_endpoint(file: UploadFile = File(...)):
    """
    Upload a medical image (X-ray, MRI, scan) as JPEG, PNG or PDF.
    Returns a plain-language explanation for the patient.
    """
    allowed_types = {"image/jpeg", "image/png", "image/jpg", "application/pdf"}
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Please upload a JPEG, PNG or PDF.",
        )

    file_bytes = await file.read()

    if len(file_bytes) > 20 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum size is 20MB.",
        )

    result = analyze_medical_image(file_bytes, file.filename)
    return result
