"""File storage service."""
import shutil
from io import BytesIO
from uuid import uuid4
from pathlib import Path

from app.config import get_settings
from app.logging import get_logger
from app.exceptions import ValidationError, NotFoundError

logger = get_logger(__name__)


class StorageService:
    def __init__(self, base_path: str) -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.settings = get_settings()

    async def save_upload(self, file: BytesIO, filename: str, content_type: str) -> tuple[str, int]:
        ext = Path(filename).suffix
        key = f"{uuid4()}{ext}"
        path = self.base_path / key

        file.seek(0, 2)
        size = file.tell()
        file.seek(0)

        max_size = self.settings.max_file_size_mb * 1024 * 1024
        if size > max_size:
            raise ValidationError(f"File size {size} exceeds max {max_size}")

        with open(path, "wb") as f:
            shutil.copyfileobj(file, f)

        logger.info("file_saved", key=key, size=size)
        return key, size

    async def get_path(self, key: str) -> str:
        path = self.base_path / key
        if not path.exists():
            raise NotFoundError("File", key)
        return str(path)

    async def delete(self, key: str) -> bool:
        path = self.base_path / key
        if path.exists():
            path.unlink()
            return True
        return False

    async def exists(self, key: str) -> bool:
        return (self.base_path / key).exists()


_storage: StorageService | None = None


def get_storage_service() -> StorageService:
    global _storage
    if _storage is None:
        settings = get_settings()
        _storage = StorageService(settings.local_storage_path)
    return _storage