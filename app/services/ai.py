from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Protocol

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

logger = logging.getLogger(__name__)


class AIUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class AIResult:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0


class AIProvider(Protocol):
    async def complete(self, system: str, text: str) -> AIResult: ...


class OpenAICompatibleProvider:
    def __init__(self, api_key: str, base_url: str, model: str, concurrency: int) -> None:
        self.model = model
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(connect=8, read=30, write=15, pool=10),
            follow_redirects=False,
        )
        self.semaphore = asyncio.Semaphore(concurrency)

    @retry(
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError, AIUnavailableError)),
        wait=wait_exponential_jitter(initial=0.5, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def complete(self, system: str, text: str) -> AIResult:
        async with self.semaphore:
            response = await self.client.post("/chat/completions", json={
                "model": self.model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": text}],
                "temperature": 0.9,
            })
            if response.status_code in {429, 500, 502, 503, 504}:
                raise AIUnavailableError(f"AI HTTP {response.status_code}")
            response.raise_for_status()
            try:
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
            except (ValueError, KeyError, IndexError, AttributeError) as exc:
                raise AIUnavailableError("Malformed AI response") from exc
            if not content:
                raise AIUnavailableError("Empty AI response")
            usage = data.get("usage", {})
            return AIResult(content, int(usage.get("prompt_tokens", 0)), int(usage.get("completion_tokens", 0)))

    async def close(self) -> None:
        await self.client.aclose()


class AIService:
    def __init__(self, provider: OpenAICompatibleProvider | None) -> None:
        self.provider = provider

    @property
    def available(self) -> bool:
        return self.provider is not None

    async def transform(self, system: str, text: str) -> AIResult:
        if not self.provider:
            raise AIUnavailableError("AI is not configured")
        return await self.provider.complete(system, text)

    async def close(self) -> None:
        if self.provider:
            await self.provider.close()
