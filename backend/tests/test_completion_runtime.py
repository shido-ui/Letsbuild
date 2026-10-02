from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database import models_import  # noqa: F401
from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database.models import AIProvider, Credential, User
from moduleiq.services.ai import registry
from moduleiq.services.ai.providers import OpenAIProvider


def test_openai_provider_is_buildable_from_registry(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'registry.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(id=str(uuid4()), email="local@moduleiq")
        db.add(user)
        db.flush()
        provider = AIProvider(
            id="openai-provider",
            user_id=user.id,
            provider_type="openai",
            model_name="gpt-5",
            enabled=True,
        )
        db.add(provider)
        db.add(Credential(
            id=str(uuid4()),
            ai_provider_id=provider.id,
            secret_ciphertext="ciphertext",
            key_fingerprint="fingerprint",
        ))
        db.commit()

        monkeypatch.setattr(registry.CredentialCipher, "decrypt", lambda self, value: "test-key")
        built = registry.build_provider(db, provider.id)
        assert isinstance(built, OpenAIProvider)
        assert built.model == "gpt-5"


def test_foreign_provider_is_rejected_by_registry(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'registry-owner.db'}")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        user = User(id=str(uuid4()), email="foreign@example.com")
        db.add(user)
        db.flush()
        provider = AIProvider(
            id="foreign-provider",
            user_id=user.id,
            provider_type="openai",
            model_name="gpt-5",
            enabled=True,
        )
        db.add(provider)
        db.add(Credential(
            id=str(uuid4()),
            ai_provider_id=provider.id,
            secret_ciphertext="ciphertext",
            key_fingerprint="fingerprint",
        ))
        db.commit()

        try:
            registry.build_provider(db, provider.id)
        except registry.InvalidCredentialError as exc:
            assert "unavailable" in str(exc).lower()
        else:
            raise AssertionError("foreign provider was accessible")
