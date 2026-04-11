from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from patient_intake.models.database import get_db
from patient_intake.models.schemas import (
    CreateSessionRequest,
    MedicalReport,
    MessageRequest,
    MessageResponse,
    SessionResponse,
    UploadResponse,
)
from patient_intake.services import document_service, intake_service, report_service
from patient_intake.storage.file_storage import storage as default_storage

router = APIRouter(prefix="/api/v1/patient-intake", tags=["Patient Intake"])


@router.post(
    "/session",
    response_model=SessionResponse,
    status_code=201,
    summary="Créer une session d'intake patient",
)
async def create_session(
    body: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Initialise une nouvelle session d'intake et retourne un session_id."""
    return await intake_service.create_session(body.patient_id, db)


@router.post(
    "/{session_id}/message",
    response_model=MessageResponse,
    summary="Envoyer un message patient (questionnaire interactif)",
)
async def send_message(
    session_id: str,
    body: MessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Reçoit le texte du patient (réponse libre ou réponse à une question).
    Claude analyse tout le contexte accumulé (historique + documents uploadés)
    et retourne la prochaine question ou un message de suivi.
    """
    return await intake_service.process_message(session_id, body.text, db)


@router.post(
    "/{session_id}/upload",
    response_model=UploadResponse,
    summary="Uploader un ou plusieurs documents médicaux",
)
async def upload_files(
    session_id: str,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="PDF, JPG ou PNG — max 20 MB chacun"),
    db: AsyncSession = Depends(get_db),
):
    """
    Stocke les fichiers et déclenche l'extraction du contenu en arrière-plan via Claude.
    Retourne immédiatement les file_ids avec le statut 'pending'.
    """
    result = await document_service.upload_files(session_id, files, db, default_storage)

    for file_info in result.uploaded_files:
        background_tasks.add_task(
            document_service.extract_file_content,
            file_info.file_id,
            default_storage,
        )

    return result


@router.post(
    "/{session_id}/generate-report",
    response_model=MedicalReport,
    summary="Générer le compte rendu médical unifié",
)
async def generate_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Agrège tous les messages et documents de la session,
    appelle Claude pour structurer le compte rendu JSON,
    calcule le completeness_score et persiste le résultat.
    """
    return await report_service.generate_report(session_id, db)


@router.get(
    "/{session_id}/report",
    response_model=MedicalReport,
    summary="Récupérer le compte rendu généré",
)
async def get_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retourne le dernier compte rendu généré pour cette session."""
    return await report_service.get_report(session_id, db)


