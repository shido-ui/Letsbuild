from __future__ import annotations

import json
import time
from typing import Any
from urllib import error, request

from .errors import (
    InvalidCredentialError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from .provider import AIProvider, AIResponse

MAX_PROMPT_CHARS = 120_000
RETRYABLE_STATUS_CODES = {408, 409, 429, 500, 502, 503, 504}


class OpenAICompatibleProvider(AIProvider):
    provider_type = "openai_compatible"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 30,
        max_retries: int = 2,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max(0, max_retries)

    def _call(self, prompt: str) -> AIResponse:
        if not prompt or not prompt.strip():
            raise ValueError("AI prompt cannot be empty")
        if len(prompt) > MAX_PROMPT_CHARS:
            raise ValueError("AI prompt exceeds the provider input limit")

        payload = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
            }
        ).encode()

        req = request.Request(
            self.base_url + "/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "ModuleIQ/0.1",
            },
            method="POST",
        )

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with request.urlopen(req, timeout=self.timeout) as res:
                    data = json.load(res)
                break
            except error.HTTPError as exc:
                if exc.code in (401, 403):
                    raise InvalidCredentialError("Provider rejected credentials") from exc
                if exc.code not in RETRYABLE_STATUS_CODES or attempt >= self.max_retries:
                    raise ProviderUnavailableError(f"Provider HTTP {exc.code}") from exc
                last_error = exc
            except TimeoutError as exc:
                if attempt >= self.max_retries:
                    raise ProviderTimeoutError("Provider request timed out") from exc
                last_error = exc
            except OSError as exc:
                if attempt >= self.max_retries:
                    raise ProviderUnavailableError("Provider connection failed") from exc
                last_error = exc

            time.sleep(0.15 * (2**attempt))
        else:
            raise ProviderUnavailableError("Provider request failed") from last_error

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderUnavailableError("Provider returned an invalid response") from exc

        if not isinstance(content, str) or not content.strip():
            raise ProviderUnavailableError("Provider returned empty content")

        return AIResponse(self.provider_type, self.model, content, data)

    def test_connection(self) -> None:
        self._call("Reply with the single word OK.")

    def classify(self, text: str) -> AIResponse:
        return self._call("Classify this material. Return concise structured facts.\n" + text)

    def extract(self, text: str) -> AIResponse:
        return self._call("Extract structured knowledge from this source.\n" + text)

    def solve(self, text: str) -> AIResponse:
        return self._call("Solve the supplied question carefully.\n" + text)

    def verify(self, text: str) -> AIResponse:
        return self._call("Verify the supplied answer and explain discrepancies.\n" + text)

    def summarize(self, text: str) -> AIResponse:
        return self._call("Summarize the supplied material.\n" + text)

    def generate_questions(self, text: str) -> AIResponse:
        return self._call("Generate study questions from this material.\n" + text)

    def analyze_image(self, image: bytes, media_type: str) -> AIResponse:
        raise NotImplementedError(
            "Image analysis is provider-specific and remains behind the provider boundary."
        )


class OpenAIProvider(OpenAICompatibleProvider):
    provider_type = "openai"

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-5",
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 30,
    ):
        super().__init__(api_key, model, base_url, timeout)


class GeminiProvider(OpenAICompatibleProvider):
    provider_type = "gemini"

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", timeout: float = 30):
        super().__init__(
            api_key,
            model,
            "https://generativelanguage.googleapis.com/v1beta/openai",
            timeout,
        )


class LocalModelProvider(OpenAICompatibleProvider):
    provider_type = "local"

    def __init__(self, base_url: str, model: str, timeout: float = 60):
        super().__init__(
            api_key="local",
            model=model,
            base_url=base_url,
            timeout=timeout,
        )
