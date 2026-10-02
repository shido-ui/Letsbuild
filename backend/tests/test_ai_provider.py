from moduleiq.services.ai.crypto import CredentialCipher

def test_credential_cipher_round_trip(monkeypatch):
    monkeypatch.setenv("MODULEIQ_CREDENTIAL_ENCRYPTION_KEY","test-secret-key")
    from moduleiq.core.config import get_settings
    get_settings.cache_clear()
    cipher=CredentialCipher()
    ciphertext=cipher.encrypt("sk-test-secret")
    assert ciphertext != "sk-test-secret"
    assert cipher.decrypt(ciphertext)=="sk-test-secret"
    assert "sk-test-secret" not in ciphertext
