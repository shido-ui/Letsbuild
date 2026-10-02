import pytest
from moduleiq.core.config import Settings

def test_production_requires_credential_key(monkeypatch):
    monkeypatch.delenv("MODULEIQ_CREDENTIAL_ENCRYPTION_KEY", raising=False)
    with pytest.raises(ValueError, match="CREDENTIAL_ENCRYPTION_KEY"):
        Settings(environment="production", cors_origins=["https://example.com"], allowed_hosts=["example.com"])

def test_production_accepts_explicit_security_configuration(monkeypatch):
    monkeypatch.setenv("MODULEIQ_CREDENTIAL_ENCRYPTION_KEY", "test-key")
    settings=Settings(environment="production", cors_origins=["https://example.com"], allowed_hosts=["example.com"])
    assert settings.environment=="production"
    assert settings.allowed_hosts==["example.com"]
