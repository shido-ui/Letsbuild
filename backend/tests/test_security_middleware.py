from fastapi.testclient import TestClient

from moduleiq.main import app


def test_security_headers():
    client = TestClient(app)
    response = client.get("/api")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert response.headers["Content-Security-Policy"].startswith("default-src 'self'")


def test_request_id_is_returned():
    client = TestClient(app)
    response = client.get("/api", headers={"X-Request-ID": "test-security-id"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-security-id"


def test_oversized_request_is_rejected():
    client = TestClient(app)
    response = client.post(
        "/api/auth/login",
        data="x" * 32,
        headers={"Content-Length": str(300 * 1024 * 1024)},
    )
    assert response.status_code in {400, 413}
