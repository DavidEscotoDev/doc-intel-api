"""Storage service tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from io import BytesIO
from uuid import uuid4

from app.services.storage import StorageService, get_storage_service
from app.exceptions import StorageError


class TestStorageService:
    @pytest.fixture
    def storage(self, tmp_path):
        return StorageService(str(tmp_path))

    @pytest.mark.asyncio
    async def test_save_file(self, storage):
        content = b"Test content"
        file = BytesIO(content)
        key, size = await storage.save_upload(file, "test.txt", "text/plain")

        assert key.endswith(".txt")
        assert size == len(content)
        assert await storage.exists(key)

    @pytest.mark.asyncio
    async def test_get_path(self, storage):
        content = b"Test"
        file = BytesIO(content)
        key, _ = await storage.save_upload(file, "test.txt", "text/plain")
        path = await storage.get_path(key)
        assert path.endswith(key)

    @pytest.mark.asyncio
    async def test_delete(self, storage):
        content = b"Test"
        file = BytesIO(content)
        key, _ = await storage.save_upload(file, "test.txt", "text/plain")
        assert await storage.delete(key) is True
        assert not await storage.exists(key)

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, storage):
        assert await storage.delete("nonexistent.txt") is False

    @pytest.mark.asyncio
    async def test_save_preserves_content(self, storage):
        content = b"Hello, World!"
        file = BytesIO(content)
        key, _ = await storage.save_upload(file, "test.txt", "text/plain")
        path = await storage.get_path(key)
        with open(path, "rb") as f:
            assert f.read() == content

    @pytest.mark.asyncio
    async def test_size_limit(self, storage):
        storage.settings.storage.max_file_size_mb = 1
        large = b"x" * (2 * 1024 * 1024)
        file = BytesIO(large)
        with pytest.raises(StorageError):
            await storage.save_upload(file, "large.txt", "text/plain")


class TestStorageFactory:
    def test_singleton(self):
        with patch("app.services.storage.get_settings") as mock_settings:
            mock_settings.return_value.storage.local_path = "/tmp/test"
            s1 = get_storage_service()
            s2 = get_storage_service()
            assert s1 is s2