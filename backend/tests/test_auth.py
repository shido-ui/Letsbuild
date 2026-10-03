from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from moduleiq.api.auth import password_hash
from moduleiq.infrastructure.database import models_import  # noqa: F401
from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database.session import get_db
from moduleiq.main import app


def client_for(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'auth.db'}")
    Base.metadata.create_all(engine)

    def override_db():
        from sqlalchemy.orm import Session
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def test_register_login_me(tmp_path):
    client = client_for(tmp_path)
    try:
        response = client.post(
            "/api/auth/register",
            json={"username": "newuser", "email": "new@example.com", "password": "password123"},
        )
        assert response.status_code == 201
        login = client.post("/api/auth/login", data={"username": "newuser", "password": "password123"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["username"] == "newuser"
    finally:
        app.dependency_overrides.clear()


def test_invalid_login_rejected(tmp_path):
    client = client_for(tmp_path)
    try:
        response = client.post("/api/auth/login", data={"username": "missing", "password": "wrong-password"})
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_protected_api_requires_bearer_token(tmp_path):
    client = client_for(tmp_path)
    try:
        response = client.get("/api/ai/providers")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()
