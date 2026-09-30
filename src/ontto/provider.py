from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import requests


@dataclass
class LLMResponse:
    text: str
    raw: dict[str, Any]


class OpenAICompatibleProvider:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def chat(self, messages: list[dict[str, str]], temperature: float = 0.7) -> LLMResponse:
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return LLMResponse(text=data["choices"][0]["message"]["content"], raw=data)
