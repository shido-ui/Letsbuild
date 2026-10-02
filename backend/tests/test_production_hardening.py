import pytest
from moduleiq.core.config import Settings

def test_production_requires_credential_key():
    with pytest.raises(ValueError, match="CREDENTIAL_ENCRYPTION_KEY"):
        Settings(environment="production", credential_encryption_key="", cors_origins=["https://example.com"], allowed_hosts=["example.com"])

def test_production_accepts_explicit_security_configuration():
    settings=Settings(environment="production", credential_encryption_key="test-key", cors_origins=["https://example.com"], allowed_hosts=["example.com"])
    assert settings.environment=="production"
    assert settings.allowed_hosts==["example.com"]
