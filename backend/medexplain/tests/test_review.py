"""Tests for the doctor review layer."""
import pytest

from models.patient_data import PDOValidationError
from review.reviewer import approve, apply_corrections


def test_approve_sets_doctor_approved(sample_pdo):
    sample_pdo.doctor_approved = False
    sample_pdo.extraction_metadata.requires_doctor_review = False
    approved = approve(sample_pdo)
    assert approved.doctor_approved is True
    assert approved.approved_at is not None


def test_approve_with_corrections(sample_pdo):
    sample_pdo.doctor_approved = False
    sample_pdo.extraction_metadata.requires_doctor_review = False
    approved = approve(sample_pdo, corrections={"video_1_disease.severity.level": "mild"})
    assert approved.video_1_disease.severity.level == "mild"
    assert approved.doctor_approved is True


def test_apply_corrections_nested_path(sample_pdo):
    corrected = apply_corrections(sample_pdo, {"patient.first_name": "Pierre"})
    assert corrected.patient.first_name == "Pierre"
    # Original unchanged
    assert sample_pdo.patient.first_name == "Jean-Paul"


def test_approve_invalid_pdo_raises(sample_pdo):
    # Remove visual_cue from a visual scene to make PDO invalid
    for s in sample_pdo.video_1_disease.scene_plan:
        if s.type.value == "visual":
            s.visual_cue = None
            break
    sample_pdo.doctor_approved = False
    sample_pdo.extraction_metadata.requires_doctor_review = False
    with pytest.raises(PDOValidationError):
        approve(sample_pdo)
