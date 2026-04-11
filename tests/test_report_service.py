import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from patient_intake.models.schemas import MedicalReport
from patient_intake.services import report_service


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _minimal_report_dict(with_lab=False, with_lifestyle=False) -> dict:
    d = {
        "patient_id": None,
        "generated_at": "2026-04-11T00:00:00+00:00",
        "patient_profile": {
            "age": 35, "sex": "F", "weight": None, "height": None,
            "known_allergies": [], "medical_history": [],
        },
        "current_condition": {
            "primary_diagnosis": "Migraine",
            "secondary_diagnoses": [],
            "symptoms": ["maux de tête", "nausées"],
            "onset_date": None, "severity": "moderate",
            "description_summary": "Migraines récurrentes depuis 3 mois",
        },
        "treatments": {
            "current_medications": [
                {"name": "Ibuprofène", "dosage": "400mg", "frequency": "si besoin",
                 "duration": None, "prescriber": None, "start_date": None}
            ],
            "past_medications": [], "other_treatments": [],
        },
        "lab_results": [{"test_name": "NFS", "value": "4.5", "unit": "G/L", "reference_range": "4-10", "date": None, "flag": "normal"}] if with_lab else [],
        "imaging": [],
        "uploaded_documents": [],
        "lifestyle_context": {
            "activity_level": "sédentaire" if with_lifestyle else None,
            "diet_notes": None, "sleep_notes": None, "stress_level": None,
            "relevant_habits": [],
        },
        "metadata": {
            "data_sources": ["patient_input"],
            "completeness_score": 0.0,
            "missing_info": [],
            "language": "fr",
        },
    }
    return d


# ---------------------------------------------------------------------------
# _compute_completeness
# ---------------------------------------------------------------------------

def test_completeness_all_key_sections_filled():
    report = _minimal_report_dict(with_lab=True, with_lifestyle=True)
    score, missing = report_service._compute_completeness(report)
    # age+sex (0.20) + diagnosis+symptoms (0.30) + medications (0.25) + lab (0.15) + lifestyle (0.10) = 1.0
    assert score == 1.00
    assert missing == []


def test_completeness_missing_lab_and_lifestyle():
    report = _minimal_report_dict()
    score, missing = report_service._compute_completeness(report)
    # 0.20 + 0.30 + 0.25 = 0.75
    assert score == 0.75
    assert any("lab_results" in m for m in missing)
    assert any("lifestyle" in m for m in missing)


def test_completeness_empty_report():
    report = {
        "patient_profile": {},
        "current_condition": {},
        "treatments": {},
        "lab_results": [],
        "imaging": [],
        "lifestyle_context": {},
    }
    score, missing = report_service._compute_completeness(report)
    assert score == 0.0
    assert len(missing) >= 5


def test_completeness_partial_profile_half_points():
    report = _minimal_report_dict()
    report["patient_profile"]["sex"] = None  # only age filled
    score, missing = report_service._compute_completeness(report)
    assert score == 0.65  # 0.10 (partial) + 0.30 + 0.25 = 0.65
    assert any("sex" in m or "age" in m for m in missing)


# ---------------------------------------------------------------------------
# generate_report
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_generate_report_returns_valid_medical_report():
    report_data = _minimal_report_dict()

    mock_session = MagicMock()
    mock_session.id = "sess-gen"
    mock_session.patient_id = None
    mock_session.status = "active"
    mock_session.messages = [MagicMock(role="patient", content="J'ai des migraines")]
    mock_session.files = []

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.side_effect = [mock_session, None]

    db = AsyncMock()
    db.execute = AsyncMock(return_value=execute_result)
    db.add = MagicMock()
    db.commit = AsyncMock()

    with patch.object(report_service, "_call_mistral_report", return_value=report_data):
        result = await report_service.generate_report("sess-gen", db)

    assert isinstance(result, MedicalReport)
    assert result.current_condition.primary_diagnosis == "Migraine"
    assert result.metadata.data_sources == ["patient_input"]
    assert result.metadata.completeness_score > 0
    assert mock_session.status == "completed"
    db.commit.assert_called()


@pytest.mark.asyncio
async def test_generate_report_raises_404_for_unknown_session():
    from fastapi import HTTPException

    db = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=execute_result)

    with pytest.raises(HTTPException) as exc_info:
        await report_service.generate_report("nonexistent", db)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_report_raises_404_when_not_generated():
    from fastapi import HTTPException

    db = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    db.execute = AsyncMock(return_value=execute_result)

    with pytest.raises(HTTPException) as exc_info:
        await report_service.get_report("sess-no-report", db)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_report_returns_persisted_report():
    report = MedicalReport(**_minimal_report_dict())

    db_report = MagicMock()
    db_report.report_json = report.model_dump_json()

    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = db_report

    db = AsyncMock()
    db.execute = AsyncMock(return_value=execute_result)

    result = await report_service.get_report("sess-ok", db)
    assert isinstance(result, MedicalReport)
    assert result.current_condition.primary_diagnosis == "Migraine"


# ---------------------------------------------------------------------------
# _build_uploaded_docs
# ---------------------------------------------------------------------------

def test_build_uploaded_docs_extracts_summary():
    f = MagicMock()
    f.id = "file-abc"
    f.original_filename = "labo.pdf"
    f.file_type = "application/pdf"
    f.upload_date = MagicMock()
    f.upload_date.isoformat.return_value = "2026-04-11T10:00:00"
    f.storage_path = "/uploads/sess/labo.pdf"
    f.extracted_content = json.dumps({"raw_summary": "NFS normale"})

    docs = report_service._build_uploaded_docs([f])
    assert len(docs) == 1
    assert docs[0]["file_id"] == "file-abc"
    assert docs[0]["extracted_content_summary"] == "NFS normale"
