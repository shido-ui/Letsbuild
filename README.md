# ModuleIQ

Android-first, local-first AI knowledge workspace built around BYOK (Bring Your Own Key) and BYOM (Bring Your Own Material).

## Current status

Phase 0 — Source Code Forensics & Architecture Lock: **GREEN**

The repository is being built from the supplied source foundations and the locked ModuleIQ product blueprint/Figma design.

## Supplied source foundations

- MinerU 4.0.10 — production document intelligence foundation.
- KaTeX 0.19.0 — web math/LaTeX rendering.
- Huey 3.4.0 — background task/worker foundation.
- FastAPI 0.142.2 — backend/API framework foundation.

## Product rules

1. Supplied source code is reused wherever technically appropriate.
2. Figma is the visual source of truth; UI is not generated from backend/database structure.
3. No artificial MVP cutoff.
4. A phase cannot advance until its gate is green.
5. AI is a replaceable service layer, not the database.
6. User knowledge persists when AI credentials are deleted or providers are switched.
7. The primary local deployment target is Android + Termux + Web/PWA + FastAPI + SQLite/local storage.
8. Production OCR/layout/equation/table/diagram capabilities are preserved rather than replaced with a simplistic parser.

See `docs/PHASE-0-SOURCE-AUDIT.md` and `docs/ARCHITECTURE-LOCK.md` for the Phase 0 findings.
