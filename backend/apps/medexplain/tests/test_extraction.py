"""Tests for the extraction layer (Mistral call mocked)."""
import json
from unittest.mock import MagicMock, patch

import pytest

from ..extraction.extractor import extract
from ..models.patient_data import PatientDataObject


MOCK_PDO_JSON = {
    "schema_version": "1.0",
    "extraction_metadata": {
        "document_language": "fr",
        "extracted_at": "2024-03-15T10:00:00Z",
        "extraction_confidence": "high",
        "requires_doctor_review": False,
        "ambiguous_fields": [],
    },
    "patient": {"first_name": "Jean-Paul", "age": 65, "sex": "male", "known_conditions": ["hypertension"]},
    "consultation": {
        "date": "2024-03-15",
        "doctor_name": "Dr. Sophie Mercier",
        "specialty": "Neurologie",
        "facility": "Hôpital Lariboisière",
    },
    "video_1_disease": {
        "diagnosis": {
            "clinical_term": "Maladie d'Alzheimer",
            "plain_language": "Maladie d'Alzheimer débutante",
            "patient_explanation": "Votre médecin a détecté des signes précoces de la maladie d'Alzheimer.",
        },
        "what_is_happening_in_the_body": {
            "plain_language": "Des protéines anormales s'accumulent dans votre cerveau.",
            "key_concepts": [
                {"term": "Atrophie hippocampique", "plain_language": "La zone mémoire rétrécit.", "visual_cue": "MRI brain scan with hippocampus highlighted"}
            ],
        },
        "why_this_patient": {"identified_risk_factors": ["âge"], "patient_explanation": "Votre âge est un facteur de risque."},
        "test_results": [
            {"test_name": "IRM", "plain_name": "Scanner", "result_raw": "Atrophie", "result_plain": "Zone mémoire réduite.", "visual_cue": "brain MRI scan"}
        ],
        "severity": {"level": "moderate", "plain_language": "Stade modéré, traitable."},
        "scene_plan": [
            {"scene": 1, "type": "avatar", "duration_sec": 18, "content": "video_1_disease.diagnosis.patient_explanation", "visual_cue": None},
            {"scene": 2, "type": "visual", "duration_sec": 20, "content": "video_1_disease.what_is_happening_in_the_body.key_concepts.0", "visual_cue": "MRI brain scan"},
            {"scene": 3, "type": "avatar", "duration_sec": 18, "content": "video_1_disease.severity.plain_language", "visual_cue": None},
        ],
    },
    "video_2_treatment": {
        "medications": [
            {
                "name": "Donépézil", "brand_name": "Aricept", "plain_language": "Aide les cellules du cerveau.",
                "dosage": "5 mg", "frequency": "1 fois par jour", "timing": "soir", "form": "tablet",
                "with_food": False, "duration": "indéfinie", "visual_cue": "white pill photo",
            }
        ],
        "important_warnings": [{"warning": "Ne pas arrêter sans avis médical.", "severity": "high"}],
        "precautions_daily_life": ["Marchez 30 minutes par jour."],
        "warning_signs_to_watch": [{"sign": "Chute soudaine", "action": "Appelez le 15.", "urgency": "urgent"}],
        "follow_up": {
            "next_appointment": "dans 3 mois",
            "specialist": "Dr. Mercier",
            "what_to_bring": "Carnet de santé",
            "additional_referrals": [],
        },
        "scene_plan": [
            {"scene": 1, "type": "avatar", "duration_sec": 16, "content": "video_2_treatment.medications.0", "visual_cue": None},
            {"scene": 2, "type": "visual", "duration_sec": 20, "content": "video_2_treatment.medications.0", "visual_cue": "white pill photo"},
            {"scene": 3, "type": "avatar", "duration_sec": 16, "content": "video_2_treatment.follow_up", "visual_cue": None},
        ],
    },
    "safety_flags": {
        "drug_interactions_detected": False,
        "allergy_conflict": False,
        "missing_critical_info": [],
        "requires_pharmacist_review": False,
        "notes": None,
    },
}


def _make_mock_mistral_response(content: str):
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    response = MagicMock()
    response.choices = [choice]
    return response


@patch("extraction.extractor.Mistral")
def test_extract_returns_pdo(mock_mistral_cls):
    mock_client = MagicMock()
    mock_mistral_cls.return_value = mock_client
    mock_client.chat.complete.return_value = _make_mock_mistral_response(
        json.dumps(MOCK_PDO_JSON)
    )

    pdo = extract("Sample report text")

    assert isinstance(pdo, PatientDataObject)
    assert pdo.patient.first_name == "Jean-Paul"
    assert pdo.patient.age == 65
    assert pdo.video_1_disease.diagnosis.clinical_term == "Maladie d'Alzheimer"


@patch("extraction.extractor.Mistral")
def test_extract_sets_requires_doctor_review_on_safety_flags(mock_mistral_cls):
    data = dict(MOCK_PDO_JSON)
    data["safety_flags"] = {**data["safety_flags"], "drug_interactions_detected": True}

    mock_client = MagicMock()
    mock_mistral_cls.return_value = mock_client
    mock_client.chat.complete.return_value = _make_mock_mistral_response(json.dumps(data))

    pdo = extract("Sample report text")

    assert pdo.safety_flags.drug_interactions_detected is True
    assert pdo.safety_flags.requires_pharmacist_review is True
    assert pdo.extraction_metadata.requires_doctor_review is True


@patch("extraction.extractor.Mistral")
def test_extract_stamps_extracted_at_if_missing(mock_mistral_cls):
    data = dict(MOCK_PDO_JSON)
    data["extraction_metadata"] = {**data["extraction_metadata"], "extracted_at": ""}

    mock_client = MagicMock()
    mock_mistral_cls.return_value = mock_client
    mock_client.chat.complete.return_value = _make_mock_mistral_response(json.dumps(data))

    pdo = extract("Sample report text")

    assert pdo.extraction_metadata.extracted_at != ""
