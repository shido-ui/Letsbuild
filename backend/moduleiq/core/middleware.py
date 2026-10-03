from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("moduleiq.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        started = time.perf_counter()
        try:
            response = await call_next(request)
            return response
        finally:
            elapsed_ms = (time.perf_counter() - started) * 1000
            logger.info("%s %s %s %.1fms", request.method, request.url.path, getattr(locals().get("response"), "status_code", 500), elapsed_ms)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
        }
        if request.url.scheme == "https":
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        for key, value in headers.items():
            response.headers.setdefault(key, value)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 120, burst_window_seconds: int = 60, max_clients: int = 5000):
        super().__init__(app)
        self.requests_per_minute = max(1, requests_per_minute)
        self.burst_window_seconds = max(1, burst_window_seconds)
        self.max_clients = max(100, max_clients)
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _trim(self, now: float) -> None:
        cutoff = now - self.burst_window_seconds
        stale = [key for key, hits in self._hits.items() if not hits or hits[-1] < cutoff]
        for key in stale:
            self._hits.pop(key, None)
        if len(self._hits) > self.max_clients:
            for key in list(self._hits)[: len(self._hits) - self.max_clients]:
                self._hits.pop(key, None)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        now = time.monotonic()
        self._trim(now)
        key = self._client_key(request)
        hits = self._hits[key]
        cutoff = now - self.burst_window_seconds
        while hits and hits[0] < cutoff:
            hits.popleft()
        if len(hits) >= self.requests_per_minute:
            retry_after = max(1, int(hits[0] + self.burst_window_seconds - now))
            return Response(
                content='{"detail":"Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(retry_after)},
            )
        hits.append(now)
        return await call_next(request)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_body_bytes: int):
        super().__init__(app)
        self.max_body_bytes = max(1, max_body_bytes)

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        declared = request.headers.get("content-length")
        if declared:
            try:
                length = int(declared)
            except ValueError:
                return Response("Invalid Content-Length", status_code=400)
            if length > self.max_body_bytes:
                return Response("Request body too large", status_code=413)
        return await call_next(request)
