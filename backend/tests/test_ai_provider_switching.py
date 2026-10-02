from uuid import uuid4
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database import models_import  # noqa: F401
from moduleiq.infrastructure.database.models import AIProvider, Credential, User
from moduleiq.services.ai.provider_switching import activate_provider, active_provider, disconnect_provider, list_user_providers

def make_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'providers.db'}")
    @event.listens_for(engine, "connect")
    def enable_fk(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    return engine

def add_provider(db, user_id, provider_id, enabled=False):
    provider = AIProvider(id=provider_id, user_id=user_id, provider_type="local", model_name=provider_id, base_url="http://127.0.0.1:8080/v1", enabled=enabled)
    db.add(provider)
    db.flush()
    db.add(Credential(id=str(uuid4()), ai_provider_id=provider.id, secret_ciphertext="encrypted-local", key_fingerprint="fingerprint"))
    db.commit()
    return provider

def test_switching_keeps_exactly_one_active_provider(tmp_path):
    engine = make_engine(tmp_path)
    with Session(engine) as db:
        user = User(id=str(uuid4()), email="switch@example.com")
        db.add(user)
        db.commit()
        add_provider(db, user.id, "p1", enabled=True)
        add_provider(db, user.id, "p2", enabled=False)
        activate_provider(db, user.id, "p2")
        providers = list_user_providers(db, user.id)
        assert [p.id for p in providers if p.enabled] == ["p2"]
        assert active_provider(db, user.id).id == "p2"

def test_disconnect_removes_credential_but_preserves_provider_metadata(tmp_path):
    engine = make_engine(tmp_path)
    with Session(engine) as db:
        user = User(id=str(uuid4()), email="disconnect@example.com")
        db.add(user)
        db.commit()
        add_provider(db, user.id, "p1", enabled=True)
        disconnect_provider(db, user.id, "p1")
        provider = db.get(AIProvider, "p1")
        assert provider is not None
        assert provider.enabled is False
        assert db.scalar(select(Credential).where(Credential.ai_provider_id == "p1")) is None
        assert active_provider(db, user.id) is None
