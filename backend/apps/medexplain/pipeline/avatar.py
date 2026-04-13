from __future__ import annotations

import os
import subprocess
import time
import httpx
from typing import Optional, TYPE_CHECKING

from ..config import settings

if TYPE_CHECKING:
    from ..models.patient_data import PatientDataObject

DID_BASE = "https://api.d-id.com"
PRESENTER_ID = "v2_public_Alyssa_NoHands_BlackShirt_Home@Mvn6Nalx90"
POLL_INTERVAL = 5   # seconds
POLL_TIMEOUT = 300  # seconds

# Output resolution — must match visual.py so the stitcher concat works
OUT_W = 1280
OUT_H = 720
# Avatar occupies the right square; diagram panel takes the remaining left width
AVATAR_SQ = 720          # avatar square size (right side)
DIAGRAM_W = OUT_W - AVATAR_SQ  # 560px (left side)

# Maps a substring of scene_content → diagram type
_CONTENT_TO_DIAGRAM = {
    "diagnosis":        "severity",
    "severity":         "severity",
    "why_this_patient": "risk_factors",
    "medications":      "treatment",
    "follow_up":        "treatment",
}


def render_avatar_scene(
    audio_clip_path: str,
    scene_number: int,
    work_dir: str,
    pdo: Optional["PatientDataObject"] = None,
    scene_content: Optional[str] = None,
) -> str:
    """
    Upload audio → D-ID Clips → download lip-synced video →
    post-process (diagram overlay + normalise to OUT_W×OUT_H).
    Returns the path to the final scene clip.
    """
    audio_url = _upload_audio_to_did(audio_clip_path)
    clip_id = _create_clip(audio_url)
    video_url = _poll_until_done(clip_id)

    raw_path = os.path.join(work_dir, f"scene_{scene_number}_avatar_raw.mp4")
    _download(video_url, raw_path)

    output_path = os.path.join(work_dir, f"scene_{scene_number}_avatar.mp4")
    _post_process(raw_path, output_path, scene_number, work_dir, pdo, scene_content)
    return output_path


# ---------------------------------------------------------------------------
# Post-processing: diagram overlay or plain normalisation
# ---------------------------------------------------------------------------

def _post_process(
    raw_path: str,
    output_path: str,
    scene_number: int,
    work_dir: str,
    pdo: Optional["PatientDataObject"],
    scene_content: Optional[str],
) -> None:
    diagram_path = _try_generate_diagram(
        scene_number, work_dir, pdo, scene_content
    )

    if diagram_path:
        _render_split_screen(raw_path, diagram_path, output_path)
    else:
        _normalise_resolution(raw_path, output_path)


def _try_generate_diagram(
    scene_number: int,
    work_dir: str,
    pdo: Optional["PatientDataObject"],
    scene_content: Optional[str],
) -> Optional[str]:
    """
    Detect diagram type from scene_content and generate the PNG.
    Returns the PNG path, or None if no diagram applies.
    """
    if pdo is None or not scene_content:
        return None

    diagram_type = None
    for key, dtype in _CONTENT_TO_DIAGRAM.items():
        if key in scene_content:
            diagram_type = dtype
            break

    if diagram_type is None:
        return None

    from .diagrams import (
        render_severity_diagram,
        render_risk_factors_diagram,
        render_treatment_diagram,
    )

    png_path = os.path.join(work_dir, f"scene_{scene_number}_diagram.png")

    if diagram_type == "severity":
        render_severity_diagram(
            diagnosis_plain=pdo.video_1_disease.diagnosis.plain_language,
            severity_level=pdo.video_1_disease.severity.level,
            severity_plain=pdo.video_1_disease.severity.plain_language,
            output_path=png_path,
        )

    elif diagram_type == "risk_factors":
        factors = pdo.video_1_disease.why_this_patient.identified_risk_factors or []
        render_risk_factors_diagram(
            risk_factors=factors,
            patient_note=pdo.video_1_disease.why_this_patient.patient_explanation,
            output_path=png_path,
        )

    elif diagram_type == "treatment":
        meds = pdo.video_2_treatment.medications
        appt = pdo.video_2_treatment.follow_up.next_appointment
        render_treatment_diagram(
            medications=meds,
            next_appointment=appt,
            output_path=png_path,
        )

    return png_path if os.path.exists(png_path) else None


def _render_split_screen(raw_path: str, diagram_png: str, output_path: str) -> None:
    """
    Left panel : diagram PNG  (DIAGRAM_W × OUT_H)
    Right panel: avatar video (AVATAR_SQ × AVATAR_SQ, letterboxed to OUT_H)
    Total output: OUT_W × OUT_H
    """
    filter_graph = (
        f"[0:v]scale={AVATAR_SQ}:{OUT_H}:force_original_aspect_ratio=decrease,"
        f"pad={AVATAR_SQ}:{OUT_H}:(ow-iw)/2:(oh-ih)/2:color=0x0a1628[avatar];"
        f"[1:v]scale={DIAGRAM_W}:{OUT_H}[diagram];"
        f"[diagram][avatar]hstack=inputs=2[out]"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", raw_path,
        "-i", diagram_png,
        "-filter_complex", filter_graph,
        "-map", "[out]",
        "-map", "0:a",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg split-screen failed: {result.stderr.decode()}")


def _normalise_resolution(raw_path: str, output_path: str) -> None:
    """Scale/pad avatar clip to OUT_W×OUT_H so all clips match for the stitcher."""
    cmd = [
        "ffmpeg", "-y",
        "-i", raw_path,
        "-vf", (
            f"scale={OUT_W}:{OUT_H}:force_original_aspect_ratio=decrease,"
            f"pad={OUT_W}:{OUT_H}:(ow-iw)/2:(oh-ih)/2:color=0x0a1628"
        ),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg normalise failed: {result.stderr.decode()}")


# ---------------------------------------------------------------------------
# D-ID API calls
# ---------------------------------------------------------------------------

def _upload_audio_to_did(audio_clip_path: str) -> str:
    headers = {"Authorization": f"Basic {settings.did_api_key}"}
    with open(audio_clip_path, "rb") as f:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{DID_BASE}/audios",
                headers=headers,
                files={"audio": (os.path.basename(audio_clip_path), f, "audio/mpeg")},
            )
            response.raise_for_status()
    return response.json()["url"]


def _create_clip(audio_url: str) -> str:
    headers = {
        "Authorization": f"Basic {settings.did_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "presenter_id": PRESENTER_ID,
        "script": {
            "type": "audio",
            "audio_url": audio_url,
        },
        "config": {
            "result_format": "mp4",
            "output_resolution": 1080,
        },
    }
    with httpx.Client(timeout=30.0) as client:
        response = client.post(f"{DID_BASE}/clips", headers=headers, json=payload)
        if not response.is_success:
            raise RuntimeError(
                f"D-ID create clip failed {response.status_code}: {response.text}"
            )
    return response.json()["id"]


def _poll_until_done(clip_id: str) -> str:
    url = f"{DID_BASE}/clips/{clip_id}"
    headers = {"Authorization": f"Basic {settings.did_api_key}"}
    elapsed = 0
    with httpx.Client(timeout=30.0) as client:
        while elapsed < POLL_TIMEOUT:
            response = client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            status = data.get("status")
            if status == "done":
                return data["result_url"]
            if status in ("error", "rejected"):
                raise RuntimeError(
                    f"D-ID clip {clip_id} failed (status={status}): {data}"
                )
            time.sleep(POLL_INTERVAL)
            elapsed += POLL_INTERVAL
    raise TimeoutError(f"D-ID clip {clip_id} did not complete within {POLL_TIMEOUT}s")


def _download(url: str, output_path: str) -> None:
    with httpx.Client(timeout=120.0) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=8192):
                    f.write(chunk)
