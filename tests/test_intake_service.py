import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from patient_intake.models.schemas import SessionResponse, MessageResponse


@pytest.mark.asyncio
async def test_create_session_returns_session_response():
    from patient_intake.services import intake_service

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    result = await intake_service.create_session("patient-42", db)

    assert isinstance(result, SessionResponse)
    assert result.patient_id == "patient-42"
    assert result.status == "active"
    assert result.session_id  # non-empty UUID
    db.add.assert_called_once()
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_create_session_accepts_null_patient_id():
    from patient_intake.services import intake_service

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    result = await intake_service.create_session(None, db)
    assert result.patient_id is None


@pytest.mark.asyncio
async def test_process_message_stores_both_turns_and_returns_response():
    from patient_intake.services import intake_service

    mock_session = MagicMock()
    mock_session.id = "sess-1"
    mock_session.messages = []
    mock_session.files = []

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    with patch.object(intake_service, "_load_session", return_value=mock_session), \
         patch.object(intake_service, "_call_mistral", return_value={
             "response": "Depuis combien de temps avez-vous ces symptômes ?",
             "is_intake_complete": False,
         }):
        result = await intake_service.process_message("sess-1", "J'ai mal à la tête", db)

    assert isinstance(result, MessageResponse)
    assert result.response_text == "Depuis combien de temps avez-vous ces symptômes ?"
    assert result.is_intake_complete is False
    assert db.add.call_count == 2  # patient message + assistant response
    db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_process_message_marks_complete_when_claude_says_so():
    from patient_intake.services import intake_service

    mock_session = MagicMock()
    mock_session.id = "sess-2"
    mock_session.messages = []
    mock_session.files = []

    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()

    with patch.object(intake_service, "_load_session", return_value=mock_session), \
         patch.object(intake_service, "_call_mistral", return_value={
             "response": "Merci, vous pouvez générer votre rapport.",
             "is_intake_complete": True,
         }):
        result = await intake_service.process_message("sess-2", "Non, pas d'allergie", db)

    assert result.is_intake_complete is True


def test_build_doc_context_no_files():
    from patient_intake.services.intake_service import _build_doc_context

    result = _build_doc_context([])
    assert "Aucun document" in result


def test_build_doc_context_with_extracted_file():
    import json
    from patient_intake.services.intake_service import _build_doc_context

    f = MagicMock()
    f.original_filename = "ordonnance.pdf"
    f.file_type = "application/pdf"
    f.extraction_status = "done"
    f.extracted_content = json.dumps({"raw_summary": "Prescription d'ibuprofène 400mg"})

    result = _build_doc_context([f])
    assert "ordonnance.pdf" in result
    assert "ibuprofène" in result


@pytest.mark.asyncio
async def test_process_message_raises_404_for_unknown_session():
    from fastapi import HTTPException
    from patient_intake.services import intake_service

    db = AsyncMock()
    with patch.object(intake_service, "_load_session", side_effect=HTTPException(status_code=404, detail="not found")):
        with pytest.raises(HTTPException) as exc_info:
            await intake_service.process_message("bad-id", "hello", db)
    assert exc_info.value.status_code == 404
