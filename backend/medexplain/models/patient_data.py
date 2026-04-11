from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator

from models.scene import SceneDefinition, SceneType


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------

class ExtractionMetadata(BaseModel):
    document_language: str
    extracted_at: str  # ISO 8601
    extraction_confidence: str  # "high" | "medium" | "low"
    requires_doctor_review: bool
    ambiguous_fields: List[str] = Field(default_factory=list)


class Patient(BaseModel):
    first_name: str
    age: int
    sex: str  # "male" | "female" | "other"
    known_conditions: List[str] = Field(default_factory=list)


class Consultation(BaseModel):
    date: str  # YYYY-MM-DD
    doctor_name: str
    specialty: str
    facility: str


# ---------------------------------------------------------------------------
# Video 1 sub-models
# ---------------------------------------------------------------------------

class KeyConcept(BaseModel):
    term: str
    plain_language: str
    visual_cue: str


class WhatIsHappeningInBody(BaseModel):
    plain_language: str
    key_concepts: List[KeyConcept] = Field(default_factory=list)


class WhyThisPatient(BaseModel):
    identified_risk_factors: Optional[List[str]] = None
    patient_explanation: str


class TestResult(BaseModel):
    test_name: str
    plain_name: str
    result_raw: str
    result_plain: str
    visual_cue: Optional[str] = None


class Severity(BaseModel):
    level: str  # "mild" | "moderate" | "severe"
    plain_language: str


class Diagnosis(BaseModel):
    clinical_term: str
    plain_language: str
    patient_explanation: str


class Video1Disease(BaseModel):
    diagnosis: Diagnosis
    what_is_happening_in_the_body: WhatIsHappeningInBody
    why_this_patient: WhyThisPatient
    test_results: List[TestResult] = Field(default_factory=list)
    severity: Severity
    scene_plan: List[SceneDefinition] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Video 2 sub-models
# ---------------------------------------------------------------------------

class Medication(BaseModel):
    name: str
    brand_name: Optional[str] = None
    plain_language: str
    dosage: str
    frequency: str
    timing: str
    form: str  # tablet | capsule | liquid | injection | patch | other
    with_food: bool
    duration: str
    visual_cue: str


class Warning(BaseModel):
    warning: str
    severity: str  # "high" | "medium" | "low"


class WarningSign(BaseModel):
    sign: str
    action: str
    urgency: str  # "urgent" | "medium" | "low"


class FollowUp(BaseModel):
    next_appointment: str
    specialist: str
    what_to_bring: str
    additional_referrals: List[str] = Field(default_factory=list)

    @field_validator("additional_referrals", mode="before")
    @classmethod
    def coerce_referrals_to_strings(cls, v: Any) -> List[str]:
        """Mistral sometimes returns objects instead of plain strings."""
        if not isinstance(v, list):
            return []
        result = []
        for item in v:
            if isinstance(item, str):
                result.append(item)
            elif isinstance(item, dict):
                # Join all string values into one readable string
                result.append(", ".join(str(val) for val in item.values() if val))
            else:
                result.append(str(item))
        return result


class Video2Treatment(BaseModel):
    medications: List[Medication] = Field(default_factory=list)
    important_warnings: List[Warning] = Field(default_factory=list)
    precautions_daily_life: List[str] = Field(default_factory=list)
    warning_signs_to_watch: List[WarningSign] = Field(default_factory=list)
    follow_up: FollowUp
    scene_plan: List[SceneDefinition] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Safety flags
# ---------------------------------------------------------------------------

class SafetyFlags(BaseModel):
    drug_interactions_detected: bool = False
    allergy_conflict: bool = False
    missing_critical_info: List[str] = Field(default_factory=list)
    requires_pharmacist_review: bool = False
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Top-level Patient Data Object
# ---------------------------------------------------------------------------

class PatientDataObject(BaseModel):
    schema_version: str = "1.0"
    extraction_metadata: ExtractionMetadata
    patient: Patient
    consultation: Consultation
    video_1_disease: Video1Disease
    video_2_treatment: Video2Treatment
    safety_flags: SafetyFlags
    # Set to True after the doctor has explicitly approved this PDO
    doctor_approved: bool = False
    approved_at: Optional[str] = None  # ISO 8601 timestamp


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class PDOValidationError(Exception):
    pass


def validate_pdo(pdo: PatientDataObject) -> None:
    """
    Enforce the 6 validation rules from DATA_SCHEMA.md.
    Raises PDOValidationError describing the first failure found.
    """
    for video_label, scene_plan in [
        ("video_1", pdo.video_1_disease.scene_plan),
        ("video_2", pdo.video_2_treatment.scene_plan),
    ]:
        if not scene_plan:
            raise PDOValidationError(f"{video_label}: scene_plan is empty")

        # Rule 2 — total duration ≤ 110s
        total = sum(s.duration_sec for s in scene_plan)
        if total > 110:
            raise PDOValidationError(
                f"{video_label}: total scene duration {total}s exceeds 110s"
            )

        # Rule 3 — starts and ends with avatar
        if scene_plan[0].type != SceneType.avatar:
            raise PDOValidationError(f"{video_label}: first scene must be avatar")
        if scene_plan[-1].type != SceneType.avatar:
            raise PDOValidationError(f"{video_label}: last scene must be avatar")

        # Rule 4 — no more than 2 consecutive same-type scenes
        for i in range(len(scene_plan) - 2):
            if (
                scene_plan[i].type == scene_plan[i + 1].type == scene_plan[i + 2].type
            ):
                raise PDOValidationError(
                    f"{video_label}: 3 consecutive {scene_plan[i].type} scenes starting at scene {scene_plan[i].scene}"
                )

        # Rule 5 — every visual scene has a visual_cue
        for s in scene_plan:
            if s.type == SceneType.visual and not s.visual_cue:
                raise PDOValidationError(
                    f"{video_label}: scene {s.scene} is visual but has no visual_cue"
                )

    # Rule 6 — requires_doctor_review resolved
    if pdo.extraction_metadata.requires_doctor_review and not pdo.doctor_approved:
        raise PDOValidationError(
            "requires_doctor_review is True but doctor has not approved this PDO"
        )
