# ModuleIQ v0.1.0

ModuleIQ 0.1.0 is the first consolidated release candidate of the Android-first, local-first knowledge workspace.

## Highlights
- Canonical structured knowledge pipeline.
- Persistent practice and adaptive learning loop.
- Search, review, analytics, and portability.
- BYOK/BYOM provider switching with safe disconnect.
- Local workspace isolation and production security controls.
- Installable PWA for Android/Termux workflows.
- Failure recovery and API-level E2E coverage.
- Full regression and production hardening gates.

## Verification
The release candidate is gated by the Phase 26 full-regression workflow plus the individual phase workflows through Phase 27.

## Upgrade note
Existing SQLite data remains the canonical source of truth. Apply Alembic migrations before starting the production API.
