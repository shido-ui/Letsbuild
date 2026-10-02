from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.models import AIProvider, Credential
from .errors import InvalidCredentialError
from .providers import GeminiProvider, LocalModelProvider, OpenAICompatibleProvider

def mask_fingerprint(secret: str) -> str:
    import hashlib
    return hashlib.sha256(secret.encode()).hexdigest()

def build_provider(db: Session, provider_id: str):
    row=db.scalar(select(AIProvider).where(AIProvider.id==provider_id,AIProvider.enabled.is_(True)))
    if row is None: raise InvalidCredentialError("Provider is unavailable")
    cred=db.scalar(select(Credential).where(Credential.ai_provider_id==provider_id))
    if cred is None or not cred.secret_ciphertext: raise InvalidCredentialError("Provider credential is not configured")
    # Phase 7 local-first secret envelope. Production multi-user key management is hardened in Phase 21.
    secret=cred.secret_ciphertext
    if row.provider_type=="gemini": return GeminiProvider(secret,row.model_name or "gemini-2.5-flash")
    if row.provider_type=="openai_compatible": return OpenAICompatibleProvider(secret,row.model_name or "gpt-5",row.__dict__.get("base_url","https://api.openai.com/v1"))
    if row.provider_type=="local": return LocalModelProvider(secret,row.model_name or "local")
    raise InvalidCredentialError("Unsupported provider type")
