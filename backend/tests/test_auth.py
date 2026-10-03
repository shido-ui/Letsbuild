from fastapi.testclient import TestClient

from moduleiq.main import app
from moduleiq.infrastructure.database.session import SessionLocal
from moduleiq.infrastructure.database.models import User
from moduleiq.api.auth import password_hash

client = TestClient(app)


def _user(db):
    user = User(
        id="auth-test-user",
        username="authuser",
        email="auth@example.com",
        hashed_password=password_hash.hash("correct-password"),
        display_name="Auth User",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def test_register_login_me():
    response = client.post(
        "/api/auth/register",
        json={"username": "newuser", "email": "new@example.com", "password": "password123"},
    )
    assert response.status_code == 201

    login = client.post(
        "/api/auth/login",
        data={"username": "newuser", "password": "password123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["username"] == "newuser"


def test_invalid_login_rejected():
    response = client.post(
        "/api/auth/login",
        data={"username": "missing", "password": "wrong-password"},
    )
    assert response.status_code == 401


def test_protected_api_requires_bearer_token():
    response = client.get("/api/ai/providers")
    assert response.status_code == 401
