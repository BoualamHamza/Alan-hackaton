import os

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_MODEL = "mistral-small-latest"

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./patient_intake.db")
STORAGE_PATH = os.getenv("STORAGE_PATH", "./uploads")

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
