from __future__ import annotations
import base64, hashlib
from cryptography.fernet import Fernet, InvalidToken
from moduleiq.core.config import get_settings

class CredentialCipher:
    def __init__(self):
        raw=get_settings().credential_encryption_key
        if not raw: raise RuntimeError("MODULEIQ_CREDENTIAL_ENCRYPTION_KEY is required")
        key=base64.urlsafe_b64encode(hashlib.sha256(raw.encode()).digest())
        self._fernet=Fernet(key)
    def encrypt(self, secret: str)->str: return self._fernet.encrypt(secret.encode()).decode()
    def decrypt(self, ciphertext: str)->str:
        try: return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as exc: raise RuntimeError("Credential cannot be decrypted with the configured key") from exc
