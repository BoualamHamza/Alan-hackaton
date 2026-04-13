from datetime import datetime, timezone
from typing import Any, Dict

from ..models.patient_data import PatientDataObject, PDOValidationError, validate_pdo


def apply_corrections(pdo: PatientDataObject, corrections: Dict[str, Any]) -> PatientDataObject:
    """
    Apply a flat dict of corrections to the PDO using dot-notation field paths.
    Example: {"video_1_disease.severity.level": "moderate"}
    Returns a new PatientDataObject with the corrections applied.
    """
    data = pdo.model_dump()

    for path, value in corrections.items():
        keys = path.split(".")
        node = data
        for key in keys[:-1]:
            if key.isdigit():
                node = node[int(key)]
            else:
                node = node[key]
        last_key = keys[-1]
        if last_key.isdigit():
            node[int(last_key)] = value
        else:
            node[last_key] = value

    return PatientDataObject.model_validate(data)


def approve(pdo: PatientDataObject, corrections: Dict[str, Any] | None = None) -> PatientDataObject:
    """
    Apply optional corrections, mark the PDO as doctor-approved, and validate.
    Raises PDOValidationError if the PDO is still invalid after approval.
    """
    if corrections:
        pdo = apply_corrections(pdo, corrections)

    pdo.doctor_approved = True
    pdo.approved_at = datetime.now(timezone.utc).isoformat()

    validate_pdo(pdo)
    return pdo
