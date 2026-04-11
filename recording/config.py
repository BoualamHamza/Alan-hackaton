import os

ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
ASSEMBLYAI_BASE_URL = "https://api.assemblyai.com/v2"

ALLOWED_AUDIO_TYPES = {
    "audio/mpeg",       # .mp3
    "audio/mp4",        # .m4a
    "audio/wav",        # .wav
    "audio/x-wav",
    "audio/ogg",        # .ogg
    "audio/webm",       # .webm (enregistrement browser)
    "video/webm",
}

MAX_AUDIO_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
