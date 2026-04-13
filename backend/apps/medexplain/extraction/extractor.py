import json
from datetime import datetime, timezone
from typing import List

from mistralai.client import Mistral
from mistralai.client.models import ResponseFormat

from ..config import settings
from .prompts import EXTRACTION_SYSTEM_PROMPT
from ..models.patient_data import PatientDataObject, SafetyFlags
from ..models.scene import SceneDefinition, SceneType

MAX_VIDEO_DURATION = 110  # seconds
AVATAR_MIN, AVATAR_MAX = 14, 20
VISUAL_MIN, VISUAL_MAX = 16, 24


def extract(report_text: str) -> PatientDataObject:
    """
    Send the raw medical report to Mistral and return the extracted
    PatientDataObject. Never raises on partial extraction — missing fields
    are left null and flagged for doctor review.
    """
    client = Mistral(api_key=settings.mistral_api_key, timeout_ms=120_000)

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
            {"role": "user", "content": report_text},
        ],
        response_format=ResponseFormat(type="json_object"),
        temperature=0.0,
    )

    raw_json = response.choices[0].message.content
    data = json.loads(raw_json)

    # Stamp extraction time if Mistral didn't
    if not data.get("extraction_metadata", {}).get("extracted_at"):
        data.setdefault("extraction_metadata", {})["extracted_at"] = (
            datetime.now(timezone.utc).isoformat()
        )

    pdo = PatientDataObject.model_validate(data)

    # Normalise scene plans to fit within 110s
    pdo.video_1_disease.scene_plan = _normalise_scene_plan(pdo.video_1_disease.scene_plan)
    pdo.video_2_treatment.scene_plan = _normalise_scene_plan(pdo.video_2_treatment.scene_plan)

    # Ensure safety flags cascade to requires_doctor_review
    flags: SafetyFlags = pdo.safety_flags
    if flags.drug_interactions_detected or flags.allergy_conflict:
        flags.requires_pharmacist_review = True
        pdo.extraction_metadata.requires_doctor_review = True

    if flags.missing_critical_info:
        pdo.extraction_metadata.requires_doctor_review = True

    return pdo


def _normalise_scene_plan(scenes: List[SceneDefinition]) -> List[SceneDefinition]:
    """
    If the total scene plan duration exceeds 110s, proportionally reduce each
    scene's duration while respecting the per-type min/max bounds.
    """
    if not scenes:
        return scenes

    total = sum(s.duration_sec for s in scenes)
    if total <= MAX_VIDEO_DURATION:
        return scenes

    scale = MAX_VIDEO_DURATION / total
    for s in scenes:
        raw = round(s.duration_sec * scale)
        lo, hi = (AVATAR_MIN, AVATAR_MAX) if s.type == SceneType.avatar else (VISUAL_MIN, VISUAL_MAX)
        s.duration_sec = max(lo, min(hi, raw))

    # If still over (due to clamping), trim the longest non-min scenes one second at a time
    while sum(s.duration_sec for s in scenes) > MAX_VIDEO_DURATION:
        lo_map = {SceneType.avatar: AVATAR_MIN, SceneType.visual: VISUAL_MIN}
        trimmable = [s for s in scenes if s.duration_sec > lo_map[s.type]]
        if not trimmable:
            break
        longest = max(trimmable, key=lambda s: s.duration_sec)
        longest.duration_sec -= 1

    return scenes
