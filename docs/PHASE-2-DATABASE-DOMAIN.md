# Phase 2 — Database & Domain Model

## Status
**GREEN**

## Scope
The canonical persistence layer is established before higher-level intelligence. It covers users/workspaces/knowledge bases; materials/documents/versions/pages; extracted blocks and hierarchy; equations/tables/diagrams/assets; questions/options/solutions; classification/difficulty/verification/provenance; practice/review; learner state; analytics; AI provider and credential metadata; and processing jobs/stages.

## Architecture
- SQLAlchemy 2.x ORM over SQLite for the Android/Termux-first local path.
- SQLite foreign keys are enabled on application connections.
- Alembic owns schema migration history.
- `backend/moduleiq/infrastructure/database/models.py` is the canonical domain model.
- Credential storage is represented as ciphertext/reference metadata; encryption and key-management behavior is intentionally deferred to the BYOK/security phases.
- AI-provider records are metadata only; knowledge objects do not depend on provider credentials for persistence.
- JSON metadata columns preserve engine/provider-specific details without becoming a second source of truth.

## Validation
- [x] Required product tables are represented by the ORM.
- [x] Foreign-key cascade behavior is covered by tests.
- [x] Unique constraints are declared in the canonical model.
- [x] Alembic initial migration exists with upgrade/downgrade entry points.
- [x] SQLite foreign-key enforcement is enabled.
- [x] No AI credential is required to create or retain knowledge objects.

## Phase gate
**GREEN — the canonical ModuleIQ database represents the complete Phase 2 product domain without using PDFs or AI responses as the database.**
