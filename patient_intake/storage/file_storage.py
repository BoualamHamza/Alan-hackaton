import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from patient_intake.config import STORAGE_PATH


class FileStorage(ABC):
    @abstractmethod
    async def save(self, session_id: str, filename: str, content: bytes) -> str:
        """Persist file content and return its storage path."""

    @abstractmethod
    async def load(self, storage_path: str) -> bytes:
        """Return raw bytes for a previously saved file."""

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        """Remove a file from storage."""


class LocalFileStorage(FileStorage):
    """Stores files on the local filesystem. Drop-in replacement for S3."""

    def __init__(self, base_path: str = STORAGE_PATH):
        self.base_path = Path(base_path)

    async def save(self, session_id: str, filename: str, content: bytes) -> str:
        session_dir = self.base_path / session_id
        session_dir.mkdir(parents=True, exist_ok=True)

        ext = Path(filename).suffix
        unique_name = f"{uuid.uuid4().hex}{ext}"
        file_path = session_dir / unique_name
        file_path.write_bytes(content)
        return str(file_path)

    async def load(self, storage_path: str) -> bytes:
        return Path(storage_path).read_bytes()

    async def delete(self, storage_path: str) -> None:
        path = Path(storage_path)
        if path.exists():
            path.unlink()


# Singleton used by default in the router
storage = LocalFileStorage()
