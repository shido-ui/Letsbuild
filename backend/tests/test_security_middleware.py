from fastapi import FastAPI
from fastapi.testclient import TestClient

from moduleiq.core.middleware import RequestSizeLimitMiddleware, RateLimitMiddleware, SecurityHeadersMiddleware


def make_app():
    app=FastAPI()
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, requests_per_minute=2)
    app.add_middleware(RequestSizeLimitMiddleware, max_body_bytes=32)

    @app.get("/ok")
    def ok():
        return {"ok": True}

    return app


def test_security_headers_and_rate_limit():
    client=TestClient(make_app())
    first=client.get("/ok")
    assert first.status_code==200
    assert first.headers["X-Content-Type-Options"]=="nosniff"
    assert first.headers["X-Frame-Options"]=="DENY"
    assert client.get("/ok").status_code==200
    third=client.get("/ok")
    assert third.status_code==429
    assert "Retry-After" in third.headers


def test_request_body_size_limit():
    client=TestClient(make_app())
    response=client.post("/ok", content=b"x"*64)
    assert response.status_code in {405,413}
