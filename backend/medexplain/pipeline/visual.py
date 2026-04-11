from __future__ import annotations

import os
import subprocess
from typing import Optional, TYPE_CHECKING

from config import settings

if TYPE_CHECKING:
    from models.patient_data import PatientDataObject

# Resolution to match avatar scenes
OUTPUT_WIDTH = 1280
OUTPUT_HEIGHT = 720

# Maps a substring of the scene's content field path → card renderer key.
# The content field is a dot-notation PDO field path like
# "video_2_treatment.medications" — very reliable for detection.
_CONTENT_TO_CARD = {
    # Video 1 — disease / mechanism
    "key_concepts": "key_concepts",
    "what_is_happening_in_the_body": "key_concepts",
    "diagnosis": "diagnosis",
    # Video 2 — treatment
    "medications": "medications",
    "important_warnings": "warnings",
    "precautions_daily_life": "precautions",
    "warning_signs_to_watch": "warning_signs",
    "follow_up": "follow_up",
    "test_results": "test_results",
}


def render_visual_scene(
    visual_cue: str,
    audio_clip_path: str,
    scene_number: int,
    work_dir: str,
    pdo: Optional["PatientDataObject"] = None,
    scene_content: Optional[str] = None,
) -> str:
    """
    Render a visual scene video.

    If a PDO is provided and the scene_content field maps to a known data
    type, a Pillow data card is generated. Otherwise falls back to the
    placeholder image.

    Returns the path to the rendered scene video.
    """
    image_path = os.path.join(work_dir, f"scene_{scene_number}_image.jpg")

    card_rendered = False
    if pdo is not None and scene_content:
        card_rendered = _try_render_card(pdo, scene_content, image_path)

    if not card_rendered:
        _generate_placeholder(image_path)

    output_path = os.path.join(work_dir, f"scene_{scene_number}_visual.mp4")
    _image_audio_to_video(image_path, audio_clip_path, output_path)
    return output_path


# --------------------------------------------------------------------------
# Card routing
# --------------------------------------------------------------------------

def _try_render_card(
    pdo: "PatientDataObject",
    scene_content: str,
    output_path: str,
) -> bool:
    """
    Detect which card type to render from the scene content path.
    Returns True if a card was rendered, False if no match.
    """
    from pipeline.cards import (
        render_medications_card,
        render_warnings_card,
        render_warning_signs_card,
        render_follow_up_card,
        render_precautions_card,
        render_test_results_card,
        render_key_concepts_card,
        render_diagnosis_card,
    )

    for key, card_type in _CONTENT_TO_CARD.items():
        if key not in scene_content:
            continue

        # ── Video 1 — disease / mechanism ───────────────────────────────────
        if card_type == "key_concepts":
            what = pdo.video_1_disease.what_is_happening_in_the_body
            if what.key_concepts or what.plain_language:
                render_key_concepts_card(what, output_path)
                return True

        elif card_type == "diagnosis":
            render_diagnosis_card(
                pdo.video_1_disease.diagnosis,
                pdo.video_1_disease.severity,
                output_path,
            )
            return True

        # ── Video 2 — treatment ──────────────────────────────────────────────
        elif card_type == "medications":
            meds = pdo.video_2_treatment.medications
            if meds:
                render_medications_card(meds, output_path)
                return True

        elif card_type == "warnings":
            warnings = pdo.video_2_treatment.important_warnings
            if warnings:
                render_warnings_card(warnings, output_path)
                return True

        elif card_type == "precautions":
            precs = pdo.video_2_treatment.precautions_daily_life
            if precs:
                render_precautions_card(precs, output_path)
                return True

        elif card_type == "warning_signs":
            signs = pdo.video_2_treatment.warning_signs_to_watch
            if signs:
                render_warning_signs_card(signs, output_path)
                return True

        elif card_type == "follow_up":
            render_follow_up_card(pdo.video_2_treatment.follow_up, output_path)
            return True

        elif card_type == "test_results":
            results = pdo.video_1_disease.test_results
            if results:
                render_test_results_card(results, output_path)
                return True

    return False


# --------------------------------------------------------------------------
# Placeholder + FFmpeg
# --------------------------------------------------------------------------

def _generate_placeholder(output_path: str) -> None:
    """Generate a dark blue placeholder image via FFmpeg."""
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c=0x0a1628:size={OUTPUT_WIDTH}x{OUTPUT_HEIGHT}:rate=1",
        "-frames:v", "1",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg placeholder failed: {result.stderr.decode()}")


def _image_audio_to_video(image_path: str, audio_path: str, output_path: str) -> None:
    """Combine a still image with an audio clip into a looped video."""
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-vf", (
            f"scale={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={OUTPUT_WIDTH}:{OUTPUT_HEIGHT}:(ow-iw)/2:(oh-ih)/2"
        ),
        "-shortest",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg visual scene render failed: {result.stderr.decode()}")
