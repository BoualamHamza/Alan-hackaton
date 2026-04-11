import json
from typing import List, Tuple

from mistralai.client import Mistral
from mistralai.client.models import ResponseFormat

from config import settings
from models.patient_data import PatientDataObject
from models.scene import SceneDefinition

SCRIPT_SYSTEM_PROMPT = """
You are a medical narration writer. You will receive structured patient data and a scene plan.
Your task is to write the narration text for each scene in the video.

Rules:
- Write narration that fits the duration of each scene (approximately 130 words per minute).
- Use a calm, warm, reassuring tone — like a trusted doctor speaking directly to the patient.
- Use "you" and "your" throughout.
- No Latin or Greek terms without an immediate plain-language explanation.
- Never use "unfortunately". Never say there is nothing that can be done.
- Each scene's narration must be self-contained and flow naturally into the next.
- Return ONLY a JSON array of objects: [{"scene": 1, "narration": "..."}, ...]
""".strip()


def _resolve_content(pdo_data: dict, field_path: str) -> str:
    """Walk a dot-notation path in the PDO dict and return the string value."""
    parts = field_path.split(".")
    node = pdo_data
    for part in parts:
        if part.isdigit():
            node = node[int(part)]
        elif isinstance(node, dict):
            node = node.get(part, "")
        elif isinstance(node, list):
            node = node[int(part)] if int(part) < len(node) else ""
        else:
            return ""
    if isinstance(node, dict):
        # Return the most informative string field found
        for key in ("patient_explanation", "plain_language", "result_plain", "warning", "sign"):
            if node.get(key):
                return node[key]
        return str(node)
    if isinstance(node, list):
        return " ".join(str(i) for i in node)
    return str(node) if node else ""


def generate_script(
    pdo: PatientDataObject, video_number: int
) -> Tuple[List[Tuple[int, str]], str]:
    """
    Generate narration for each scene of a video.

    Returns:
        - List of (scene_number, narration_text) pairs
        - Full concatenated script (all scenes joined)
    """
    scene_plan: List[SceneDefinition] = (
        pdo.video_1_disease.scene_plan
        if video_number == 1
        else pdo.video_2_treatment.scene_plan
    )

    pdo_data = pdo.model_dump()
    scene_contents = [
        {
            "scene": s.scene,
            "type": s.type,
            "duration_sec": s.duration_sec,
            "content_hint": _resolve_content(pdo_data, s.content),
        }
        for s in scene_plan
    ]

    user_message = json.dumps(
        {
            "patient_first_name": pdo.patient.first_name,
            "video_number": video_number,
            "scenes": scene_contents,
        },
        ensure_ascii=False,
        indent=2,
    )

    client = Mistral(api_key=settings.mistral_api_key, timeout_ms=120_000)
    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[
            {"role": "system", "content": SCRIPT_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        response_format=ResponseFormat(type="json_object"),
        temperature=0.3,
    )

    raw = response.choices[0].message.content
    data = json.loads(raw)

    # Mistral may return {"scenes": [...]} or directly [...]
    if isinstance(data, dict):
        items = data.get("scenes") or data.get("narrations") or list(data.values())[0]
    else:
        items = data

    scene_narrations: List[Tuple[int, str]] = [
        (item["scene"], item["narration"]) for item in items
    ]
    full_script = " ".join(narration for _, narration in scene_narrations)

    return scene_narrations, full_script
