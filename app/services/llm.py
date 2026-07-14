"""LLM service for document analysis."""
import asyncio
import json
from dataclasses import dataclass

import anthropic

from app.config import get_settings
from app.exceptions import ValidationError
from app.logging import get_logger

logger = get_logger(__name__)


@dataclass
class AnalysisResult:
    summary: str
    key_points: list[str]
    entities: list[str]
    sentiment: str
    topics: list[str]
    tokens_used: int
    raw: str


class LLMService:
    SYS_PROMPT = """You are an expert document analyst. Return ONLY valid JSON with:
- summary: 2-3 sentence executive summary
- key_points: 3-5 bullet points
- entities: list of named entities
- sentiment: positive/negative/neutral
- topics: main topics/themes"""

    def __init__(self) -> None:
        self.s = get_settings()
        self.client = anthropic.AsyncAnthropic(
            api_key=self.s.anthropic_api_key,
            timeout=self.s.anthropic_timeout,
            max_retries=self.s.anthropic_max_retries,
        )
        self.model = self.s.anthropic_model

    async def analyze(self, text: str) -> AnalysisResult:
        logger.info("llm_analyze_start", len=len(text))

        # Retry only the API call on transient errors
        for attempt in range(3):
            try:
                resp = await self.client.messages.create(
                    model=self.model,
                    max_tokens=self.s.anthropic_max_tokens,
                    temperature=self.s.anthropic_temperature,
                    system=self.SYS_PROMPT,
                    messages=[{"role": "user", "content": f"Analyze:\n\n{text}"}],
                )
                break
            except (
                anthropic.RateLimitError,
                anthropic.APIConnectionError,
                anthropic.APIStatusError,
            ) as e:
                if attempt == 2:
                    raise ValidationError(f"LLM failed after retries: {e}") from e
                await asyncio.sleep(2**attempt)

        raw = resp.content[0].text
        data = self._parse(raw)
        return AnalysisResult(
            summary=data["summary"],
            key_points=data["key_points"],
            entities=data["entities"],
            sentiment=data["sentiment"],
            topics=data["topics"],
            tokens_used=resp.usage.output_tokens,
            raw=raw,
        )

    def _parse(self, raw: str) -> dict:
        try:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                if "```json" in raw:
                    raw = raw.split("```json")[1].split("```")[0]
                elif "```" in raw:
                    raw = raw.split("```")[1].split("```")[0]
                data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON response: {e}") from e

        for k in ["summary", "key_points", "entities", "sentiment", "topics"]:
            if k not in data:
                raise ValidationError(f"Missing field: {k}")

        # Normalize sentiment
        if data["sentiment"].lower() not in {"positive", "negative", "neutral"}:
            data["sentiment"] = "neutral"
        else:
            data["sentiment"] = data["sentiment"].lower()

        return data


_llm: LLMService | None = None


def get_llm_service() -> LLMService:
    global _llm
    if _llm is None:
        _llm = LLMService()
    return _llm
