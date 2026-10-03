from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database import models_import  # noqa: F401
from moduleiq.infrastructure.database.models import AIProvider, Credential, User
from moduleiq.main import app
from moduleiq.core.dependencies import get_current_user
from moduleiq.infrastructure.database.session import get_db
import moduleiq.api.ai as ai_api


def make_db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'api.db'}")
    Base.metadata.create_all(engine)
    return engine


def test_provider_input_accepts_openai():
    body = ai_api.ProviderIn(
        provider_type="openai",
        model_name="gpt-5",
        base_url="https://api.openai.com/v1",
        api_key="test-key",
    )
    assert body.provider_type == "openai"


def test_provider_mutations_are_owner_scoped(tmp_path, monkeypatch):
    engine = make_db(tmp_path)
    with Session(engine) as db:
        user = User(id=str(uuid4()), email="owner@example.com")
        other = User(id=str(uuid4()), email="other@example.com")
        db.add_all([user, other])
        db.flush()
        provider = AIProvider(
            id="owned-provider",
            user_id=other.id,
            provider_type="local",
            model_name="local",
            base_url="http://127.0.0.1:8080/v1",
            enabled=False,
        )
        db.add(provider)
        db.add(Credential(
            id=str(uuid4()),
            ai_provider_id=provider.id,
            secret_ciphertext="cipher",
            key_fingerprint="fingerprint",
        ))
        db.commit()

    def override_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(ai_api, "_user", lambda db: db.scalar(
        __import__("sqlalchemy").select(User).where(User.email == "owner@example.com")
    ))
    client = TestClient(app)
    try:
        response = client.post("/api/ai/providers/owned-provider/test")
        assert response.status_code == 404
        response = client.delete("/api/ai/providers/owned-provider")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
