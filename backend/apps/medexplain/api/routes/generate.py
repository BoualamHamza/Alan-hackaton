import os

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...config import settings
from ...models.patient_data import PatientDataObject, PDOValidationError, validate_pdo
from ...script.generator import generate_script
from ...pipeline.orchestrator import run_pipeline

router = APIRouter(prefix="/generate", tags=["generation"])


class GenerateRequest(BaseModel):
    pdo: PatientDataObject


class GenerateResponse(BaseModel):
    video_1_path: str
    video_2_path: str


@router.post("", response_model=GenerateResponse)
async def generate_videos(body: GenerateRequest) -> GenerateResponse:
    """
    Layers 3 + 4: Generate narration scripts and produce both videos.
    The PDO must already be doctor-approved (doctor_approved=True).
    Returns local file paths to the two rendered .mp4 files.
    """
    pdo = body.pdo

    if not pdo.doctor_approved:
        raise HTTPException(
            status_code=422,
            detail="PDO must be approved by the doctor before generating videos. Use /review/approve first.",
        )

    try:
        validate_pdo(pdo)
    except PDOValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Script generation (Layer 3)
    try:
        _, script_v1 = generate_script(pdo, video_number=1)
        _, script_v2 = generate_script(pdo, video_number=2)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Script generation failed: {exc}") from exc

    # Video production (Layer 4)
    os.makedirs(settings.output_dir, exist_ok=True)
    try:
        video_1_path, video_2_path = await run_pipeline(
            pdo=pdo,
            video_1_script=script_v1,
            video_2_script=script_v2,
            output_dir=settings.output_dir,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Video production failed: {exc}") from exc

    return GenerateResponse(video_1_path=video_1_path, video_2_path=video_2_path)

