"""Ollama API client for the consolidator."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    """Response from the LLM."""
    content: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int
    model: str


class OllamaClient:
    """Client for Ollama's OpenAI-compatible API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen2.5:7b",
        timeout: float = 60.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def is_available(self) -> bool:
        """Check if Ollama server is reachable."""
        try:
            resp = requests.get(self.base_url, timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def chat(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Send a chat completion request.

        Uses /v1/chat/completions (OpenAI-compatible endpoint).
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 300,
            "temperature": 0,
            "stop": ["---", "\n\n\n"],
        }

        start = time.monotonic()
        resp = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload,
            timeout=self.timeout,
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        resp.raise_for_status()

        data = resp.json()
        choice = data["choices"][0]
        content = choice["message"]["content"].strip()

        usage = data.get("usage", {})
        return LLMResponse(
            content=content,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            latency_ms=latency_ms,
            model=data.get("model", self.model),
        )
