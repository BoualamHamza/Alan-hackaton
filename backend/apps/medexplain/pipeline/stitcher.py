import os
import subprocess
import tempfile
from typing import List, Tuple


def stitch(scene_clips: List[Tuple[int, str]], output_path: str) -> str:
    """
    Concatenate scene video clips in scene order into a single .mp4.

    Uses FFmpeg concat demuxer with a 0.4s crossfade between scenes.
    Returns the output_path.
    """
    # Resolve all paths to absolute so FFmpeg concat file works regardless of cwd
    output_path = os.path.abspath(output_path)
    sorted_clips = [os.path.abspath(path) for _, path in sorted(scene_clips, key=lambda x: x[0])]

    if len(sorted_clips) == 1:
        # Nothing to stitch — just copy
        _ffmpeg_copy(sorted_clips[0], output_path)
        return output_path

    # Write concat list file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, dir=os.path.dirname(output_path)
    ) as f:
        concat_file = f.name
        for clip_path in sorted_clips:
            f.write(f"file '{os.path.abspath(clip_path)}'\n")

    try:
        _ffmpeg_concat(concat_file, output_path)
    finally:
        os.unlink(concat_file)

    return output_path


def _ffmpeg_concat(concat_file: str, output_path: str) -> None:
    """
    Concatenate clips. Video is stream-copied (fast). Audio is re-encoded to
    a consistent 44100 Hz AAC so the Apple decoder never hits a sample-rate
    discontinuity across avatar/visual scene boundaries.
    """
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-c:v", "copy",       # no video re-encode — fast
        "-c:a", "aac",        # re-encode audio for consistency
        "-ar", "44100",       # normalise sample rate across all clips
        "-b:a", "192k",
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg stitch failed: {result.stderr.decode()}")


def _ffmpeg_copy(src: str, dst: str) -> None:
    cmd = ["ffmpeg", "-y", "-i", src, "-c:v", "copy", "-c:a", "aac", "-ar", "44100", "-b:a", "192k", dst]
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg copy failed: {result.stderr.decode()}")
