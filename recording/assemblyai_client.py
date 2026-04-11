"""
Client AssemblyAI — upload audio, transcription, summarization.
"""

import asyncio

import httpx
from fastapi import HTTPException

from recording.config import ASSEMBLYAI_API_KEY, ASSEMBLYAI_BASE_URL


def _headers() -> dict:
    if not ASSEMBLYAI_API_KEY:
        raise HTTPException(status_code=500, detail="ASSEMBLYAI_API_KEY non configurée")
    return {"authorization": ASSEMBLYAI_API_KEY}


async def upload_audio(audio_bytes: bytes) -> str:
    """Upload le fichier audio sur AssemblyAI, retourne l'upload_url."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(
                f"{ASSEMBLYAI_BASE_URL}/upload",
                headers={**_headers(), "content-type": "application/octet-stream"},
                content=audio_bytes,
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"AssemblyAI injoignable : {exc}")

    if not resp.is_success:
        raise HTTPException(status_code=502, detail=f"AssemblyAI upload error {resp.status_code}: {resp.text}")

    return resp.json()["upload_url"]


async def request_transcription(upload_url: str) -> str:
    """Soumet la transcription + résumé, retourne le transcript_id."""
    payload = {
        "audio_url": upload_url,
        "language_detection": True,   # détecte automatiquement FR ou EN
        "summarization": True,
        "summary_model": "informative",
        "summary_type": "bullets",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{ASSEMBLYAI_BASE_URL}/transcript",
                headers=_headers(),
                json=payload,
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"AssemblyAI injoignable : {exc}")

    if not resp.is_success:
        raise HTTPException(status_code=502, detail=f"AssemblyAI transcript error {resp.status_code}: {resp.text}")

    return resp.json()["id"]


async def poll_transcript(transcript_id: str, max_wait_seconds: int = 120) -> dict:
    """Poll jusqu'à ce que la transcription soit prête. Retourne le résultat complet."""
    url = f"{ASSEMBLYAI_BASE_URL}/transcript/{transcript_id}"
    elapsed = 0

    async with httpx.AsyncClient(timeout=15.0) as client:
        while elapsed < max_wait_seconds:
            try:
                resp = await client.get(url, headers=_headers())
            except httpx.RequestError as exc:
                raise HTTPException(status_code=502, detail=f"AssemblyAI polling error : {exc}")

            data = resp.json()
            status = data.get("status")

            if status == "completed":
                return data
            if status == "error":
                raise HTTPException(status_code=502, detail=f"AssemblyAI transcription échouée : {data.get('error')}")

            await asyncio.sleep(3)
            elapsed += 3

    raise HTTPException(status_code=504, detail="Timeout AssemblyAI — transcription trop longue (>2 min)")
