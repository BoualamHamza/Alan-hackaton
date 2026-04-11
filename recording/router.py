from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from recording.assemblyai_client import upload_audio, request_transcription, poll_transcript
from recording.extractor import extract_medical_info
from recording.config import ALLOWED_AUDIO_TYPES, MAX_AUDIO_SIZE_BYTES

router = APIRouter(prefix="/api/v1/recording", tags=["Recording"])


class RecordingAnalysis(BaseModel):
    transcript: str
    summary: str
    prefill: dict  # { diagnosis, symptoms, medications, instructions }


@router.post(
    "/analyze",
    response_model=RecordingAnalysis,
    summary="Analyser un enregistrement de consultation médicale",
)
async def analyze_recording(
    file: UploadFile = File(..., description="Audio de la consultation — mp3, m4a, wav, webm (max 25 MB)"),
):
    """
    Upload un enregistrement audio d'une consultation médicale.

    Pipeline :
    1. Upload sur AssemblyAI
    2. Transcription automatique (FR/EN détecté automatiquement)
    3. Résumé en bullet points
    4. Extraction structurée : diagnostic, symptômes, médicaments, instructions

    Retourne un objet `prefill` prêt à injecter dans le questionnaire patient.
    """
    # Validate type
    if file.content_type not in ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Format non supporté : {file.content_type}. Acceptés : mp3, m4a, wav, ogg, webm",
        )

    # Validate size
    audio_bytes = await file.read()
    if len(audio_bytes) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="Fichier trop volumineux (max 25 MB)")

    # 1. Upload sur AssemblyAI
    upload_url = await upload_audio(audio_bytes)

    # 2. Lancer la transcription
    transcript_id = await request_transcription(upload_url)

    # 3. Attendre le résultat (poll toutes les 3s, max 2 min)
    result = await poll_transcript(transcript_id)

    transcript = result.get("text") or ""
    summary = result.get("summary") or ""

    if not transcript:
        raise HTTPException(status_code=422, detail="Transcription vide — audio inaudible ou trop court")

    # 4. Extraire les infos médicales via Mistral
    prefill = await extract_medical_info(transcript, summary)

    return RecordingAnalysis(
        transcript=transcript,
        summary=summary,
        prefill=prefill,
    )
