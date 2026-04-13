"""Tests for PDO validation rules."""
import pytest

from ..models.patient_data import PatientDataObject, PDOValidationError, validate_pdo
from ..models.scene import SceneDefinition, SceneType


def test_validate_pdo_passes_valid(sample_pdo):
    validate_pdo(sample_pdo)  # should not raise


def test_validate_total_duration_exceeded(sample_pdo):
    # Add a large scene to video 1 to exceed 110s
    extra = SceneDefinition(
        scene=6, type=SceneType.avatar, duration_sec=20,
        content="video_1_disease.severity.plain_language"
    )
    sample_pdo.video_1_disease.scene_plan.append(extra)
    # Total is now 18+20+18+20+18+20 = 114 > 110
    with pytest.raises(PDOValidationError, match="exceeds 110s"):
        validate_pdo(sample_pdo)


def test_validate_must_start_with_avatar(sample_pdo):
    sample_pdo.video_1_disease.scene_plan[0].type = SceneType.visual
    sample_pdo.video_1_disease.scene_plan[0].visual_cue = "some image"
    with pytest.raises(PDOValidationError, match="first scene must be avatar"):
        validate_pdo(sample_pdo)


def test_validate_must_end_with_avatar(sample_pdo):
    sample_pdo.video_1_disease.scene_plan[-1].type = SceneType.visual
    sample_pdo.video_1_disease.scene_plan[-1].visual_cue = "some image"
    with pytest.raises(PDOValidationError, match="last scene must be avatar"):
        validate_pdo(sample_pdo)


def test_validate_three_consecutive_same_type(sample_pdo):
    # Insert an extra avatar so we get 3 in a row at scenes 3,4,5
    sample_pdo.video_1_disease.scene_plan[3].type = SceneType.avatar
    sample_pdo.video_1_disease.scene_plan[3].visual_cue = None
    with pytest.raises(PDOValidationError, match="3 consecutive"):
        validate_pdo(sample_pdo)


def test_validate_visual_scene_missing_cue(sample_pdo):
    for s in sample_pdo.video_1_disease.scene_plan:
        if s.type == SceneType.visual:
            s.visual_cue = None
            break
    with pytest.raises(PDOValidationError, match="no visual_cue"):
        validate_pdo(sample_pdo)


def test_validate_requires_doctor_review_not_approved(sample_pdo):
    sample_pdo.extraction_metadata.requires_doctor_review = True
    sample_pdo.doctor_approved = False
    with pytest.raises(PDOValidationError, match="doctor has not approved"):
        validate_pdo(sample_pdo)
