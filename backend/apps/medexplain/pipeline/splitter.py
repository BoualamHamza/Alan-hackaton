import os
import subprocess
from typing import List, Tuple

from ..models.scene import SceneDefinition


def split_audio(
    audio_bytes: bytes,
    alignment: List[dict],
    scene_plan: List[SceneDefinition],
    work_dir: str,
) -> List[Tuple[int, str]]:
    """
    Split the full audio track into per-scene clips.

    Uses word-level alignment to find precise millisecond boundaries,
    then cuts with FFmpeg (stream copy — no re-encode).

    Returns: list of (scene_number, clip_path) sorted by scene number.
    """
    # Write full audio to disk
    full_audio_path = os.path.join(work_dir, "full_audio.mp3")
    with open(full_audio_path, "wb") as f:
        f.write(audio_bytes)

    # Calculate scene boundaries from alignment + scene durations
    boundaries = _compute_boundaries(alignment, scene_plan)

    clips: List[Tuple[int, str]] = []
    for scene_def, (start_ms, end_ms) in zip(scene_plan, boundaries):
        clip_path = os.path.join(work_dir, f"scene_{scene_def.scene}_audio.mp3")
        _ffmpeg_cut(full_audio_path, clip_path, start_ms, end_ms)
        clips.append((scene_def.scene, clip_path))

    return clips


def _compute_boundaries(
    alignment: List[dict], scene_plan: List[SceneDefinition]
) -> List[Tuple[int, int]]:
    """
    Map scene durations to millisecond boundaries in the audio track.

    Strategy: use word timestamps to find the word boundary closest to the
    target cumulative time for each scene split point.
    """
    if not alignment:
        # Fallback: split by duration proportionally
        boundaries = []
        cursor_ms = 0
        for scene in scene_plan:
            end_ms = cursor_ms + scene.duration_sec * 1000
            boundaries.append((cursor_ms, end_ms))
            cursor_ms = end_ms
        return boundaries

    total_audio_ms = int(alignment[-1]["end_time"] * 1000)
    total_declared_sec = sum(s.duration_sec for s in scene_plan)

    boundaries = []
    cursor_ms = 0

    for i, scene in enumerate(scene_plan):
        if i == len(scene_plan) - 1:
            # Last scene takes everything remaining
            boundaries.append((cursor_ms, total_audio_ms))
        else:
            target_ms = cursor_ms + int(
                (scene.duration_sec / total_declared_sec) * total_audio_ms
            )
            # Snap to nearest word boundary
            snap_ms = _nearest_word_boundary(alignment, target_ms)
            boundaries.append((cursor_ms, snap_ms))
            cursor_ms = snap_ms

    return boundaries


def _nearest_word_boundary(alignment: List[dict], target_ms: int) -> int:
    """Return the end_time (ms) of the word closest to target_ms."""
    best = None
    best_diff = float("inf")
    for word_info in alignment:
        end_ms = int(word_info["end_time"] * 1000)
        diff = abs(end_ms - target_ms)
        if diff < best_diff:
            best_diff = diff
            best = end_ms
    return best or target_ms


def _ffmpeg_cut(src: str, dst: str, start_ms: int, end_ms: int) -> None:
    """Cut a segment from src audio into dst using FFmpeg stream copy."""
    start_s = start_ms / 1000
    duration_s = (end_ms - start_ms) / 1000
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_s),
        "-t", str(duration_s),
        "-i", src,
        "-c", "copy",
        dst,
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg audio cut failed: {result.stderr.decode()}"
        )
