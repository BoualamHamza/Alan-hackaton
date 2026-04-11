"""
Utilise Mistral pour extraire diagnostic + symptômes depuis la transcription.
"""

import json

import httpx
from fastapi import HTTPException

from patient_intake.config import MISTRAL_API_KEY, MISTRAL_API_URL, MISTRAL_MODEL

_SYSTEM_PROMPT = """Tu es un assistant médical qui analyse la transcription d'une consultation médicale.
Extrait uniquement les informations médicales clés mentionnées par le médecin.

Réponds UNIQUEMENT avec un JSON valide :
{
  "diagnosis": "diagnostic principal posé par le médecin, ou null si non mentionné",
  "symptoms": ["symptôme 1", "symptôme 2"],
  "medications": ["médicament 1", "médicament 2"],
  "instructions": ["instruction 1", "instruction 2"]
}

Règles :
- Ne jamais inventer d'informations non présentes dans la transcription
- Si une information est absente, mettre null ou []
- Rester factuel, pas d'interprétation
"""


async def extract_medical_info(transcript: str, summary: str) -> dict:
    """Extrait diagnostic + symptômes depuis la transcription via Mistral."""
    if not MISTRAL_API_KEY:
        raise HTTPException(status_code=500, detail="MISTRAL_API_KEY non configurée")

    content = f"RÉSUMÉ DE LA CONSULTATION :\n{summary}\n\nTRANSCRIPTION COMPLÈTE :\n{transcript[:4000]}"

    payload = {
        "model": MISTRAL_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                MISTRAL_API_URL,
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=502, detail=f"Mistral injoignable : {exc}")

    if not resp.is_success:
        raise HTTPException(status_code=502, detail=f"Mistral error {resp.status_code}: {resp.text}")

    raw = resp.json()["choices"][0]["message"]["content"]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"diagnosis": None, "symptoms": [], "medications": [], "instructions": []}
