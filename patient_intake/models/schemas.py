from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class CreateSessionRequest(BaseModel):
    patient_id: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    patient_id: Optional[str]
    created_at: datetime
    status: str


# ---------------------------------------------------------------------------
# Conversation
# ---------------------------------------------------------------------------

class MessageRequest(BaseModel):
    text: str


class MessageResponse(BaseModel):
    session_id: str
    response_text: str
    is_intake_complete: bool = False


# ---------------------------------------------------------------------------
# File upload
# ---------------------------------------------------------------------------

class UploadedFileInfo(BaseModel):
    file_id: str
    original_filename: str
    file_type: str
    upload_date: datetime
    extraction_status: str


class UploadResponse(BaseModel):
    session_id: str
    uploaded_files: List[UploadedFileInfo]


# ---------------------------------------------------------------------------
# Medical Report — sub-models
# ---------------------------------------------------------------------------

class PatientProfile(BaseModel):
    age: Optional[int] = None
    sex: Optional[str] = None
    weight: Optional[str] = None
    height: Optional[str] = None
    known_allergies: List[str] = Field(default_factory=list)
    medical_history: List[str] = Field(default_factory=list)


class CurrentCondition(BaseModel):
    primary_diagnosis: Optional[str] = None
    secondary_diagnoses: List[str] = Field(default_factory=list)
    symptoms: List[str] = Field(default_factory=list)
    onset_date: Optional[str] = None
    severity: Optional[str] = None
    description_summary: Optional[str] = None


class Medication(BaseModel):
    name: str
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    prescriber: Optional[str] = None
    start_date: Optional[str] = None


class Treatments(BaseModel):
    current_medications: List[Medication] = Field(default_factory=list)
    past_medications: List[Medication] = Field(default_factory=list)
    other_treatments: List[str] = Field(default_factory=list)


class LabResult(BaseModel):
    test_name: str
    value: Optional[str] = None
    unit: Optional[str] = None
    reference_range: Optional[str] = None
    date: Optional[str] = None
    flag: Optional[Literal["normal", "high", "low", "critical"]] = None


class ImagingResult(BaseModel):
    type: Optional[str] = None
    date: Optional[str] = None
    body_part: Optional[str] = None
    findings_summary: Optional[str] = None
    original_file_id: Optional[str] = None


class UploadedDocumentSummary(BaseModel):
    file_id: str
    original_filename: str
    file_type: str
    upload_date: str
    extracted_content_summary: Optional[str] = None
    storage_path: str


class LifestyleContext(BaseModel):
    activity_level: Optional[str] = None
    diet_notes: Optional[str] = None
    sleep_notes: Optional[str] = None
    stress_level: Optional[str] = None
    relevant_habits: List[str] = Field(default_factory=list)


class ReportMetadata(BaseModel):
    data_sources: List[str] = Field(default_factory=list)
    completeness_score: float = 0.0
    missing_info: List[str] = Field(default_factory=list)
    language: str = "fr"


# ---------------------------------------------------------------------------
# Medical Report — root model (contrat d'interface avec les autres services)
# ---------------------------------------------------------------------------

class MedicalReport(BaseModel):
    patient_id: Optional[str] = None
    generated_at: str
    patient_profile: PatientProfile = Field(default_factory=PatientProfile)
    current_condition: CurrentCondition = Field(default_factory=CurrentCondition)
    treatments: Treatments = Field(default_factory=Treatments)
    lab_results: List[LabResult] = Field(default_factory=list)
    imaging: List[ImagingResult] = Field(default_factory=list)
    uploaded_documents: List[UploadedDocumentSummary] = Field(default_factory=list)
    lifestyle_context: LifestyleContext = Field(default_factory=LifestyleContext)
    metadata: ReportMetadata = Field(default_factory=ReportMetadata)
