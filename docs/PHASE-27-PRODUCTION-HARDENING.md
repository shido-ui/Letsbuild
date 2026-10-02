# Phase 27 — Production Hardening

Production mode now has explicit configuration requirements and safer defaults.

- Credential encryption key is mandatory outside development/test.
- Production CORS must be explicitly configured rather than inheriting development localhost defaults.
- Interactive API documentation is disabled in production.
- Browser security headers remain enabled; HSTS is enabled in production.
- Readiness performs a database probe.
- API 500 responses do not echo internal exception text.
- Request correlation IDs are returned through X-Request-ID.
