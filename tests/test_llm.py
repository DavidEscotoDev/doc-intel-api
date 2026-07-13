"""LLM service tests."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

from app.services.llm import LLMService, get_llm_service, AnalysisResult
from app.exceptions import LLMError
import anthropic


class TestLLMService:
    @pytest.fixture
    def mock_anthropic(self):
        with patch("anthropic.AsyncAnthropic") as mock:
            client = AsyncMock()
            mock.return_value = client
            yield client

    @pytest.fixture
    def service(self, mock_anthropic):
        return LLMService()

    @pytest.mark.asyncio
    async def test_analyze_success(self, service, mock_anthropic):
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text=json.dumps({
            "summary": "Test summary",
            "key_points": ["P1", "P2"],
            "entities": ["Entity1"],
            "sentiment": "positive",
            "topics": ["Topic1"],
        }))]
        mock_resp.usage = MagicMock(input_tokens=100, output_tokens=150)
        mock_anthropic.messages.create.return_value = mock_resp

        result = await service.analyze("Test document")

        assert isinstance(result, AnalysisResult)
        assert result.summary == "Test summary"
        assert result.sentiment == "positive"
        assert result.tokens_used == 150

    @pytest.mark.asyncio
    async def test_analyze_json_in_markdown(self, service, mock_anthropic):
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text='```json\n{"summary": "Test", "key_points": [], "entities": [], "sentiment": "neutral", "topics": []}\n```')]
        mock_resp.usage = MagicMock(input_tokens=50, output_tokens=80)
        mock_anthropic.messages.create.return_value = mock_resp

        result = await service.analyze("Test")
        assert result.summary == "Test"

    @pytest.mark.asyncio
    async def test_analyze_invalid_json(self, service, mock_anthropic):
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text="Not JSON")]
        mock_resp.usage = MagicMock(input_tokens=10, output_tokens=20)
        mock_anthropic.messages.create.return_value = mock_resp

        with pytest.raises(LLMError) as exc:
            await service.analyze("Test")
        assert "Invalid JSON" in str(exc.value)

    @pytest.mark.asyncio
    async def test_analyze_missing_fields(self, service, mock_anthropic):
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text='{"summary": "Test"}')]
        mock_resp.usage = MagicMock(input_tokens=10, output_tokens=20)
        mock_anthropic.messages.create.return_value = mock_resp

        with pytest.raises(LLMError) as exc:
            await service.analyze("Test")
        assert "Missing field" in str(exc.value)

    @pytest.mark.asyncio
    async def test_analyze_normalizes_sentiment(self, service, mock_anthropic):
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text=json.dumps({
            "summary": "Test", "key_points": [], "entities": [],
            "sentiment": "POSITIVE", "topics": [],
        }))]
        mock_resp.usage = MagicMock(input_tokens=10, output_tokens=20)
        mock_anthropic.messages.create.return_value = mock_resp

        result = await service.analyze("Test")
        assert result.sentiment == "positive"

    @pytest.mark.asyncio
    async def test_analyze_rate_limit(self, service, mock_anthropic):
        import anthropic
        mock_anthropic.messages.create.side_effect = anthropic.RateLimitError(
            "Rate limited", response=MagicMock(status_code=429), body={}
        )
        with pytest.raises(LLMError) as exc:
            await service.analyze("Test")
        assert "Rate limited" in str(exc.value)

    @pytest.mark.asyncio
    async def test_analyze_retry(self, service, mock_anthropic):
        import anthropic
        mock_resp = MagicMock()
        mock_resp.content = [MagicMock(text=json.dumps({
            "summary": "Test", "key_points": [], "entities": [],
            "sentiment": "neutral", "topics": [],
        }))]
        mock_resp.usage = MagicMock(input_tokens=10, output_tokens=20)
        mock_anthropic.messages.create.side_effect = [
            anthropic.APIConnectionError(request=None),
            anthropic.APIConnectionError(request=None),
            mock_resp,
        ]

        result = await service.analyze("Test")
        assert result.summary == "Test"
        assert mock_anthropic.messages.create.call_count == 3


class TestLLMFactory:
    def test_singleton(self):
        with patch("anthropic.AsyncAnthropic"):
            s1 = get_llm_service()
            s2 = get_llm_service()
            assert s1 is s2