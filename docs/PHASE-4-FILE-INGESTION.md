# Phase 4 — File Ingestion & BYOM

## Status
**GREEN**

## Delivered
- Real PDF multipart upload endpoint: `POST /api/ingestion/upload`
- Knowledge-base listing/creation endpoints
- Local-first workspace ownership bootstrap
- Streaming upload to disk with SHA-256 hashing
- 250 MB configurable upload ceiling
- PDF magic/signature validation
- PDF parse validation and page count
- PDF metadata capture
- Safe filename normalization
- Content-addressed storage under workspace/knowledge-base boundaries
- Material → Document → DocumentVersion records
- ProcessingJob and ordered ProcessingStage records
- Duplicate detection by SHA-256 within a knowledge base
- Explicit duplicate policy: reject or reuse
- Huey preparation worker boundary with retry policy
- SQLite FTS5 search index with deterministic rebuild fingerprinting
- Durable vector embedding storage with model/dimension/content-hash metadata
- In-process cosine vector retrieval for semantic search without a native vector extension
- Job status endpoint: `GET /api/ingestion/jobs/{job_id}`
- Frontend Upload screen now sends real files to the backend
- Frontend Processing screen polls and displays the real processing job

## Ownership model
Authentication is not yet implemented because it belongs to the later security/authentication phase. Until then, Phase 4 uses a deterministic local workspace owner (`local@moduleiq`) so every material has an actual User → Workspace → KnowledgeBase ownership chain rather than an unowned global file.

## Validation
- [x] Normal one-page PDF
- [x] Invalid PDF signature
- [x] Corrupt/unparseable PDF path
- [x] Upload-size enforcement
- [x] SHA-256 duplicate detection
- [x] Material/document/version/job creation
- [x] Processing stage creation
- [x] FTS5 indexing and safe query construction
- [x] Vector storage round-trip and cosine retrieval
- [x] Frontend-to-backend upload path
- [x] Frontend CI build
- [x] Backend Phase 4 CI tests

## Deliberate boundary
MinerU is **not** invoked in this phase. Phase 4 owns intake, validation, storage, ownership, and job tracking. Phase 5 connects the supplied MinerU production document engine to the queued processing boundary.

## Phase gate
**GREEN — a real uploaded PDF becomes a tracked ModuleIQ processing job with metadata and knowledge-base association.**
