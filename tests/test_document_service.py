import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import UploadFile

from patient_intake.models.schemas import UploadedFileInfo, UploadResponse


def _make_upload_file(filename: str, content_type: str, content: bytes = b"fake content") -> MagicMock:
    f = MagicMock(spec=UploadFile)
    f.filename = filename
    f.content_type = content_type
    f.read = AsyncMock(return_value=content)
    return f


@pytest.mark.asyncio
async def test_upload_files_rejects_unsupported_mime():
    from fastapi import HTTPException
    from patient_intake.services import document_service

    bad_file = _make_upload_file("report.txt", "text/plain")
    db = AsyncMock()
    storage = AsyncMock()

    # Session exists
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = MagicMock()
    db.execute = AsyncMock(return_value=execute_result)

    with pytest.raises(HTTPException) as exc_info:
        await document_service.upload_files("sess-1", [bad_file], db, storage)
    assert exc_info.value.status_code == 415


@pytest.mark.asyncio
async def test_upload_files_rejects_empty_file():
    from fastapi import HTTPException
    from patient_intake.services import document_service

    empty_file = _make_upload_file("empty.pdf", "application/pdf", b"")
    db = AsyncMock()
    storage = AsyncMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = MagicMock()
    db.execute = AsyncMock(return_value=execute_result)

    with pytest.raises(HTTPException) as exc_info:
        await document_service.upload_files("sess-1", [empty_file], db, storage)
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_upload_files_rejects_oversized_file():
    from fastapi import HTTPException
    from patient_intake.services import document_service
    from patient_intake.config import MAX_FILE_SIZE_BYTES

    big_file = _make_upload_file("big.pdf", "application/pdf", b"x" * (MAX_FILE_SIZE_BYTES + 1))
    db = AsyncMock()
    storage = AsyncMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = MagicMock()
    db.execute = AsyncMock(return_value=execute_result)

    with pytest.raises(HTTPException) as exc_info:
        await document_service.upload_files("sess-1", [big_file], db, storage)
    assert exc_info.value.status_code == 413


@pytest.mark.asyncio
async def test_upload_files_raises_404_for_unknown_session():
    from fastapi import HTTPException
    from patient_intake.services import document_service

    f = _make_upload_file("doc.pdf", "application/pdf")
    db = AsyncMock()
    storage = AsyncMock()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None  # session not found
    db.execute = AsyncMock(return_value=execute_result)

    with pytest.raises(HTTPException) as exc_info:
        await document_service.upload_files("bad-sess", [f], db, storage)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_extract_file_content_marks_failed_on_storage_error():
    from patient_intake.services import document_service

    storage = AsyncMock()
    storage.load.side_effect = RuntimeError("disque plein")

    mock_file = MagicMock()
    mock_file.id = "file-1"
    mock_file.storage_path = "/uploads/sess/abc.pdf"
    mock_file.file_type = "application/pdf"
    mock_file.extraction_status = "pending"

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = mock_file

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=execute_result)
    mock_db.commit = AsyncMock()

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_db)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("patient_intake.services.document_service.async_session_factory", return_value=mock_ctx):
        await document_service.extract_file_content("file-1", storage)

    assert mock_file.extraction_status == "failed"


@pytest.mark.asyncio
async def test_extract_file_content_marks_done_on_success():
    from patient_intake.services import document_service

    storage = AsyncMock()
    storage.load = AsyncMock(return_value=b"%PDF fake content")

    mock_file = MagicMock()
    mock_file.id = "file-2"
    mock_file.storage_path = "/uploads/sess/doc.pdf"
    mock_file.file_type = "application/pdf"
    mock_file.extraction_status = "pending"

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = mock_file

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=execute_result)
    mock_db.commit = AsyncMock()

    mock_ctx = MagicMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_db)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    extracted_data = {"raw_summary": "Ordonnance de Doliprane 500mg", "document_type": "prescription"}

    with patch("patient_intake.services.document_service.async_session_factory", return_value=mock_ctx), \
         patch.object(document_service, "_call_mistral_extraction", return_value=extracted_data):
        await document_service.extract_file_content("file-2", storage)

    assert mock_file.extraction_status == "done"
    assert "Doliprane" in mock_file.extracted_content
