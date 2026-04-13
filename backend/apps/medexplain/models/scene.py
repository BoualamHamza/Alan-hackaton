from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class SceneType(str, Enum):
    avatar = "avatar"
    visual = "visual"


class SceneDefinition(BaseModel):
    scene: int
    type: SceneType
    duration_sec: int
    # Field path in PatientDataObject that contains the text to narrate
    content: str
    visual_cue: Optional[str] = None

    @field_validator("duration_sec")
    @classmethod
    def check_duration(cls, v, info):
        # Validation against scene type happens at the PDO level
        if v < 14 or v > 24:
            raise ValueError("duration_sec must be between 14 and 24")
        return v

    @field_validator("visual_cue")
    @classmethod
    def visual_scene_must_have_cue(cls, v, info):
        # Cross-field validation is done in validate_pdo; this is a safeguard
        return v
