from __future__ import annotations

from typing import Any

from openai import OpenAI


class LLMClient:
    """Small OpenAI-compatible chat-completions wrapper."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str | None = None,
        base_url: str | None = None,
        client: Any | None = None,
    ) -> None:
        self.model = model
        self._client: Any = client or OpenAI(api_key=api_key, base_url=base_url)

    def complete(self, system: str, user: str, *, temperature: float = 0.7) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
        )
        content = response.choices[0].message.content
        return content or ""
