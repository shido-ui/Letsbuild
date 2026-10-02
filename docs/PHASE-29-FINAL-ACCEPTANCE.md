# Phase 29 — Final Acceptance

Final acceptance confirms the ModuleIQ release candidate as a coherent full-stack system.

Acceptance gates:
1. Backend compiles.
2. Alembic migrations apply cleanly.
3. Complete pytest suite passes.
4. API E2E journey passes.
5. Security/data-isolation checks pass.
6. Failure/recovery checks pass.
7. Frontend production build passes.
8. PWA manifest/service worker are emitted.
9. Release notes and release workflow exist.
10. Production settings enforce explicit security configuration.

Final acceptance does not publish a release automatically. Publishing remains an intentional tag action through the Phase 28 release workflow.
