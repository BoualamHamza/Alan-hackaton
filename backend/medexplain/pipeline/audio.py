import base64
from typing import List, Tuple

from elevenlabs import ElevenLabs
from elevenlabs.types import VoiceSettings

from config import settings


def generate_audio(full_script: str) -> Tuple[bytes, List[dict]]:
    """
    Send the full narration script to ElevenLabs and return:
      - audio_bytes: the full audio track as raw bytes (mp3)
      - alignment: list of {"word": str, "start_time": float, "end_time": float}
    """
    client = ElevenLabs(api_key=settings.elevenlabs_api_key)

    result = client.text_to_speech.convert_with_timestamps(
        voice_id=settings.elevenlabs_voice_id,
        text=full_script,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True,
        ),
    )

    audio_bytes = base64.b64decode(result.audio_base_64)

    alignment = _build_word_alignment(result.alignment)

    return audio_bytes, alignment


def _build_word_alignment(alignment) -> List[dict]:
    """
    ElevenLabs returns character-level alignment.
    Accepts either the SDK object or a plain dict (for tests).
    Rebuilds word-level boundaries by grouping on spaces.
    """
    if alignment is None:
        return []

    if isinstance(alignment, dict):
        chars = alignment.get("characters") or []
        starts = alignment.get("character_start_times_seconds") or []
        ends = alignment.get("character_end_times_seconds") or []
    else:
        chars = alignment.characters or []
        starts = alignment.character_start_times_seconds or []
        ends = alignment.character_end_times_seconds or []

    if not chars:
        return []

    words = []
    current_word: List[str] = []
    word_start = None

    for char, start, end in zip(chars, starts, ends):
        if char in (" ", "\n"):
            if current_word:
                words.append({
                    "word": "".join(current_word),
                    "start_time": word_start,
                    "end_time": end,
                })
                current_word = []
                word_start = None
        else:
            if word_start is None:
                word_start = start
            current_word.append(char)

    if current_word:
        words.append({
            "word": "".join(current_word),
            "start_time": word_start,
            "end_time": ends[-1] if ends else 0,
        })

    return words
