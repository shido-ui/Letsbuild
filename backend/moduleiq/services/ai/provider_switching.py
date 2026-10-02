from __future__ import annotations
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.models import AIProvider, Credential

def list_user_providers(db: Session, user_id: str) -> list[AIProvider]:
    return list(db.scalars(select(AIProvider).where(AIProvider.user_id == user_id).order_by(AIProvider.created_at)).all())

def active_provider(db: Session, user_id: str) -> AIProvider | None:
    return db.scalar(select(AIProvider).where(AIProvider.user_id == user_id, AIProvider.enabled.is_(True)))

def activate_provider(db: Session, user_id: str, provider_id: str) -> AIProvider:
    provider = db.scalar(select(AIProvider).where(AIProvider.id == provider_id, AIProvider.user_id == user_id))
    if provider is None:
        raise ValueError("Provider not found")
    credential = db.scalar(select(Credential).where(Credential.ai_provider_id == provider.id))
    if credential is None or not credential.secret_ciphertext:
        raise ValueError("Provider credential is not configured")
    db.execute(update(AIProvider).where(AIProvider.user_id == user_id).values(enabled=False))
    provider.enabled = True
    db.commit()
    db.refresh(provider)
    return provider

def disconnect_provider(db: Session, user_id: str, provider_id: str) -> AIProvider:
    provider = db.scalar(select(AIProvider).where(AIProvider.id == provider_id, AIProvider.user_id == user_id))
    if provider is None:
        raise ValueError("Provider not found")
    provider.enabled = False
    db.execute(delete(Credential).where(Credential.ai_provider_id == provider.id))
    db.commit()
    db.refresh(provider)
    return provider
