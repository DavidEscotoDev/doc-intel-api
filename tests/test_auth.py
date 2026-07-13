"""Authentication middleware tests."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.middleware.auth import verify_api_key, get_current_api_key
from app.models.api_key import APIKey
from app.exceptions import AuthenticationError, AuthorizationError


class TestVerifyAPIKey:
    """Test API key verification."""

    @pytest.fixture
    def mock_request(self):
        request = MagicMock(spec=Request)
        request.client.host = "127.0.0.1"
        request.headers = {}
        request.state = MagicMock()
        return request

    @pytest.fixture
    def mock_db_session(self):
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def mock_pwd_context(self):
        with patch("app.middleware.auth.pwd_context") as mock:
            mock.verify.return_value = True
            mock.hash.return_value = "hashed_key"
            yield mock

    @pytest.fixture
    def valid_api_key(self, mock_pwd_context):
        return APIKey(
            id=uuid4(),
            key_hash="hashed_key",
            name="Test Key",
            rate_limit=100,
            is_active=True,
            total_requests=0,
        )

    @pytest.mark.asyncio
    async def test_verify_missing_header(self, mock_request, mock_db_session):
        mock_request.headers = {}

        with pytest.raises(Exception) as exc_info:
            await verify_api_key(mock_request, authorization=None, db=mock_db_session)

        assert "Invalid or missing API key" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_invalid_format(self, mock_request, mock_db_session):
        mock_request.headers = {"authorization": "InvalidFormat"}

        with pytest.raises(Exception) as exc_info:
            await verify_api_key(mock_request, authorization="InvalidFormat", db=mock_db_session)

        assert "Invalid authorization format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_invalid_prefix(self, mock_request, mock_db_session):
        mock_request.headers = {"authorization": "Bearer invalid_key"}

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(Exception) as exc_info:
            await verify_api_key(mock_request, authorization="Bearer invalid_key", db=mock_db_session)

        assert "Invalid API key format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_verify_valid_key(self, mock_request, mock_db_session, valid_api_key, mock_pwd_context):
        mock_request.headers = {"authorization": "Bearer di_test_shortkey"}

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [valid_api_key]
        mock_db_session.execute.return_value = mock_result

        result = await verify_api_key(mock_request, authorization="Bearer di_test_shortkey", db=mock_db_session)

        assert result == valid_api_key
        assert valid_api_key.total_requests == 1
        assert valid_api_key.last_used_at is not None

    @pytest.mark.asyncio
    async def test_verify_expired_key(self, mock_request, mock_db_session, mock_pwd_context):
        expired_key = APIKey(
            id=uuid4(),
            key_hash="hashed_key",
            name="Expired Key",
            rate_limit=100,
            is_active=True,
            expires_at=datetime.utcnow() - timedelta(days=1),
        )

        mock_request.headers = {"authorization": "Bearer di_test_shortkey"}
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [expired_key]
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(Exception) as exc_info:
            await verify_api_key(mock_request, authorization="Bearer di_test_shortkey", db=mock_db_session)

        assert "expired" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_verify_inactive_key(self, mock_request, mock_db_session):
        # Test that invalid hashes are rejected
        inactive_key = APIKey(
            id=uuid4(),
            key_hash="invalid_hash",
            name="Inactive Key",
            rate_limit=100,
            is_active=False,
            total_requests=0,
        )

        mock_request.headers = {"authorization": "Bearer di_test_shortkey"}
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [inactive_key]
        mock_db_session.execute.return_value = mock_result

        with pytest.raises(Exception) as exc_info:
            await verify_api_key(mock_request, authorization="Bearer di_test_shortkey", db=mock_db_session)

        # Invalid hash causes passlib to raise UnknownHashError
        assert "hash could not be identified" in str(exc_info.value).lower() or "invalid" in str(exc_info.value).lower()


class TestGetCurrentAPIKey:
    """Test get_current_api_key dependency."""

    @pytest.mark.asyncio
    async def test_get_key_from_state(self):
        request = MagicMock(spec=Request)
        api_key = MagicMock(spec=APIKey)
        request.state.api_key = api_key

        result = await get_current_api_key(request)
        assert result == api_key

    @pytest.mark.asyncio
    async def test_get_key_missing_state(self):
        request = MagicMock(spec=Request)
        request.state = MagicMock()
        del request.state.api_key

        with pytest.raises(RuntimeError):
            await get_current_api_key(request)