import asyncio
import os
import tempfile
from typing import List, Tuple

from models.patient_data import PatientDataObject
from models.scene import SceneDefinition, SceneType
from pipeline.audio import generate_audio
from pipeline.splitter import split_audio
from pipeline.avatar import render_avatar_scene
from pipeline.visual import render_visual_scene
from pipeline.stitcher import stitch


async def run_pipeline(
    pdo: PatientDataObject,
    video_1_script: str,
    video_2_script: str,
    output_dir: str,
) -> Tuple[str, str]:
    """
    Run both video pipelines concurrently.
    Returns (video_1_path, video_2_path).
    """
    # Run sequentially to avoid concurrent ElevenLabs voice conflicts (409 already_running)
    video_1_path = await _run_single_video(
        pdo=pdo,
        script=video_1_script,
        scene_plan=pdo.video_1_disease.scene_plan,
        video_number=1,
        output_dir=output_dir,
    )
    video_2_path = await _run_single_video(
        pdo=pdo,
        script=video_2_script,
        scene_plan=pdo.video_2_treatment.scene_plan,
        video_number=2,
        output_dir=output_dir,
    )
    return video_1_path, video_2_path


async def _run_single_video(
    pdo: PatientDataObject,
    script: str,
    scene_plan: List[SceneDefinition],
    video_number: int,
    output_dir: str,
) -> str:
    """
    Full pipeline for one video:
      1. Generate audio (ElevenLabs)
      2. Split audio into per-scene clips
      3. Render all scenes in parallel (D-ID for avatar, FFmpeg for visual)
      4. Stitch into final .mp4
    """
    work_dir = tempfile.mkdtemp(prefix=f"medexplain_v{video_number}_", dir=output_dir)

    # Stage 1 + 2: audio generation and splitting are synchronous/blocking — run in executor
    loop = asyncio.get_event_loop()

    audio_bytes, alignment = await loop.run_in_executor(
        None, generate_audio, script
    )
    audio_clips: List[Tuple[int, str]] = await loop.run_in_executor(
        None, split_audio, audio_bytes, alignment, scene_plan, work_dir
    )

    audio_clip_map = {scene_num: path for scene_num, path in audio_clips}

    # Stage 3: render all scenes in parallel
    render_tasks = []
    for scene_def in scene_plan:
        clip_path = audio_clip_map[scene_def.scene]
        if scene_def.type == SceneType.avatar:
            render_tasks.append(
                loop.run_in_executor(
                    None,
                    render_avatar_scene,
                    clip_path,
                    scene_def.scene,
                    work_dir,
                    pdo,
                    scene_def.content,
                )
            )
        else:
            render_tasks.append(
                loop.run_in_executor(
                    None,
                    render_visual_scene,
                    scene_def.visual_cue,
                    clip_path,
                    scene_def.scene,
                    work_dir,
                    pdo,
                    scene_def.content,
                )
            )

    rendered_paths = await asyncio.gather(*render_tasks)

    scene_clips = [
        (scene_def.scene, path)
        for scene_def, path in zip(scene_plan, rendered_paths)
    ]

    # Stage 4: stitch
    output_path = os.path.join(output_dir, f"video_{video_number}.mp4")
    await loop.run_in_executor(None, stitch, scene_clips, output_path)

    return output_path
