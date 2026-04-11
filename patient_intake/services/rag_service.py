"""
Proxy vers le service RAG du collègue (branche AssistantIA).
Endpoint cible : POST {RAG_SERVICE_URL}/chat
Utilisé quand le patient n'a pas encore consulté de médecin.
"""

import httpx
from fastapi import HTTPException

from patient_intake.config import RAG_SERVICE_URL


async def ask_rag(session_id: str, message: str) -> dict:
    """
    Envoie un message au service RAG MedBridge et retourne sa réponse.

    Retourne :
    {
        "session_id": str,
        "response": str,
        "sources": list[str]
    }
    """
    payload = {
        "session_id": session_id,
        "message": message,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(
                f"{RAG_SERVICE_URL}/chat",
                json=payload,
                headers={"Content-Type": "application/json"},
            )
        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Service RAG inaccessible ({RAG_SERVICE_URL}). "
                    "Vérifiez que le service AssistantIA est démarré."
                ),
            )
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Timeout du service RAG")

    if not resp.is_success:
        raise HTTPException(
            status_code=502,
            detail=f"Erreur service RAG {resp.status_code} : {resp.text[:200]}",
        )

    return resp.json()
