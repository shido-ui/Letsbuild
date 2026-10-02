import io
import json
from urllib.error import HTTPError

import pytest

from moduleiq.services.ai.errors import InvalidCredentialError, ProviderUnavailableError
from moduleiq.services.ai.providers import OpenAIProvider, OpenAICompatibleProvider


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return json.dumps(self.payload).encode()

    def __iter__(self):
        return iter(())


def test_openai_provider_preserves_provider_identity(monkeypatch):
    monkeypatch.setattr(
        "moduleiq.services.ai.providers.request.urlopen",
        lambda *_args, **_kwargs: FakeResponse(
            {"choices": [{"message": {"content": "OK"}}]}
        ),
    )
    response = OpenAIProvider("secret")._call("hello")
    assert response.provider == "openai"
    assert response.model == "gpt-5"
    assert response.content == "OK"


def test_provider_rejects_empty_prompt():
    provider = OpenAICompatibleProvider("secret", "model")
    with pytest.raises(ValueError, match="cannot be empty"):
        provider._call("   ")


def test_provider_rejects_oversized_prompt():
    provider = OpenAICompatibleProvider("secret", "model")
    with pytest.raises(ValueError, match="input limit"):
        provider._call("x" * 120_001)


def test_provider_maps_auth_failure(monkeypatch):
    def reject(*_args, **_kwargs):
        raise HTTPError(
            "https://example.test",
            401,
            "unauthorized",
            {},
            io.BytesIO(b""),
        )

    monkeypatch.setattr("moduleiq.services.ai.providers.request.urlopen", reject)
    with pytest.raises(InvalidCredentialError):
        OpenAICompatibleProvider("secret", "model")._call("hello")


def test_provider_retries_transient_failure(monkeypatch):
    calls = {"count": 0}

    def transient_then_success(*_args, **_kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise HTTPError(
                "https://example.test",
                503,
                "unavailable",
                {},
                io.BytesIO(b""),
            )
        return FakeResponse({"choices": [{"message": {"content": "OK"}}]})

    monkeypatch.setattr(
        "moduleiq.services.ai.providers.request.urlopen",
        transient_then_success,
    )
    monkeypatch.setattr("moduleiq.services.ai.providers.time.sleep", lambda *_: None)

    response = OpenAICompatibleProvider("secret", "model")._call("hello")
    assert response.content == "OK"
    assert calls["count"] == 2


def test_provider_reports_invalid_response(monkeypatch):
    monkeypatch.setattr(
        "moduleiq.services.ai.providers.request.urlopen",
        lambda *_args, **_kwargs: FakeResponse({"choices": []}),
    )
    with pytest.raises(ProviderUnavailableError):
        OpenAICompatibleProvider("secret", "model")._call("hello")
