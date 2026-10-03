from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database import models_import  # noqa: F401
from moduleiq.infrastructure.database.models import User
from moduleiq.api.auth import router as auth_router
from fastapi import FastAPI

app = FastAPI()
app.include_router(auth_router, prefix="/api")


def test_register_login_and_me(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'auth.db'}")
    Base.metadata.create_all(engine)

    def override_db():
        with Session(engine) as db:
            yield db

    from moduleiq.api.auth import get_db
    app.dependency_overrides[get_db] = override_db

    client = TestClient(app)
    payload = {"username": "shido", "email": "shido@example.com", "password": "correct-horse-battery"}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["username"] == "shido"

    login = client.post(
        "/api/auth/login",
        data={"username": "shido", "password": payload["password"]},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "shido@example.com"

    bad = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid"})
    assert bad.status_code == 401

    with Session(engine) as db:
        users = db.query(User).all()
        assert len(users) == 1
        assert users[0].id


def test_invalid_credentials_are_rejected(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'auth-invalid.db'}")
    Base.metadata.create_all(engine)

    def override_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides.clear()
    app.dependency_overrides[get_db] = override_db
    client = TestClient(app)
    client.post(
        "/api/auth/register",
        json={"username": "tester", "email": "tester@example.com", "password": "valid-password"},
    )
    response = client.post(
        "/api/auth/login",
        data={"username": "tester", "password": "wrong-password"},
    )
    assert response.status_code == 401
    app.dependency_overrides.clear()
