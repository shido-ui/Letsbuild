# Phase 0 — Source Code Forensics & Architecture Lock

Status: **GREEN**

## 1. Repository baseline

Target repository: `shido-ui/Letsbuild`

GitHub inspection confirmed that the repository exists, is public, has default branch `main`, and is currently empty (GitHub reports repository size 0 and the tree API returns an empty-repository 409).

Therefore Phase 0 establishes the architecture and audit record before application source is introduced.

## 2. Supplied source inventory

| Source | Audited version | Files in supplied archive | Primary role | Decision |
|---|---:|---:|---|---|
| MinerU | 4.0.10 | 1,151 | Production document intelligence | Integrate as the core document engine; adapt/wrap at ModuleIQ boundaries |
| KaTeX | 0.19.0 | 722 | Browser/server math rendering | Integrate as the math rendering subsystem; do not fork unnecessarily |
| Huey | 3.4.0 | 138 | Background jobs/workers | Integrate as ModuleIQ worker/task infrastructure |
| FastAPI | 0.142.2 | 3,170 | HTTP/API framework | Use as ModuleIQ backend framework; do not fork framework internals unless a demonstrated need appears |

File counts include tests/docs/assets contained in the supplied archives.

## 3. MinerU findings

The supplied MinerU tree contains dedicated document-processing infrastructure including:

- PDF analysis pipeline.
- OCR implementations.
- PP-DocLayoutV2 layout processing.
- Formula recognition/FormulaNet.
- Table recognition/structure recovery.
- Figure/image handling.
- VLM runtime/contracts and multiple VLM backends.
- Parser/API server.
- Document library (doclib).
- Background ingest/parse/scan workers.
- SQLite database support.
- FTS5 content/filename search.
- Search service.
- Structured rendering/output paths.
- CLI/API/WebUI/server entry points.
- A substantial automated test suite.

Important source modules audited include:

- `mineru/backend/analysis/pdf/pipeline.py`
- `mineru/model/layout/pp_doclayoutv2.py`
- `mineru/model/ocr/*`
- `mineru/model/mfr/pp_formulanet/*`
- `mineru/model/table/*`
- `mineru/doclib/core/fts.py`
- `mineru/doclib/background/parse_worker.py`
- `mineru/doclib/services/search_svc.py`
- `mineru/parser/*`
- `mineru/kit/*`

The supplied project itself declares Python `>=3.10,<3.15` and includes dependencies for FastAPI, Pydantic, ONNX Runtime, OpenAI-compatible access, image/document handling, and optional Torch/VLM stacks.

### Integration decision

MinerU is the most valuable supplied implementation and remains the production extraction foundation. ModuleIQ will place a stable normalization boundary around MinerU so the application does not become coupled to every internal extractor representation.

The MinerU source is not to be replaced by a lightweight PDF parser.

## 4. KaTeX findings

The supplied KaTeX source is version 0.19.0 and contains:

- TypeScript source.
- TeX parser.
- HTML/MathML tree generation.
- Environments/functions/macros.
- Browser rendering.
- Auto-render extension.
- mhchem support.
- Accessibility rendering support.
- Type definitions.
- Extensive test infrastructure.

### Integration decision

KaTeX is the ModuleIQ mathematical rendering subsystem. Extracted LaTeX remains structured knowledge data and is rendered in the frontend with KaTeX.

We will not duplicate KaTeX's parser/rendering logic in ModuleIQ.

## 5. Huey findings

The supplied Huey source is version 3.4.0 and contains:

- Task API.
- Consumer/worker implementation.
- Storage backends.
- Registry.
- Serialization.
- Signals.
- Asyncio integration.
- SQLite-related support via contrib.
- Redis/Valkey-related support.
- Extensive tests.

### Integration decision

Huey provides the ModuleIQ background-job foundation for long-running document ingestion, AI enrichment, verification, indexing, export/import and recovery jobs.

ModuleIQ owns the job domain model and user-facing progress state; Huey owns execution mechanics.

## 6. FastAPI findings

The supplied FastAPI source is version 0.142.2 and contains:

- Routing.
- Dependency injection.
- Request/response handling.
- Validation.
- OpenAPI generation.
- Security/authentication primitives.
- WebSocket support.
- Extensive tests and documentation.

The audited project requires Python >=3.10 and depends on Starlette and Pydantic.

### Integration decision

FastAPI is the ModuleIQ backend framework. We do not create a competing HTTP framework.

ModuleIQ application code remains separate from FastAPI framework internals so framework updates remain possible.

## 7. License / attribution findings

### MinerU

MinerU uses Apache License 2.0 with additional terms. The supplied license specifically requires clear/prominent MinerU attribution when providing online services based on MinerU, and contains commercial-use thresholds.

This obligation is locked into the ModuleIQ release checklist.

### KaTeX

MIT license. Copyright/permission notice requirements must be preserved where applicable.

### Huey

MIT license. Copyright/permission notice requirements must be preserved where applicable.

### FastAPI

MIT license. Copyright/permission notice requirements must be preserved where applicable.

No source license is being silently removed.

## 8. Static validation performed

The supplied Python source trees successfully passed Python bytecode compilation:

- MinerU package: **PASS**
- Huey package: **PASS**
- FastAPI package: **PASS**

KaTeX `package.json` successfully parsed as valid JSON.

This is a Phase 0 syntax/integrity smoke check, not a claim that every upstream test suite has been executed.

## 9. Design audit baseline

The previously inspected ModuleIQ Figma file remains the visual source of truth.

Locked top-level product frames include:

1. Dashboard
2. Upload & Analyze
3. AI Processing
4. Library
5. Document Detail
6. Questions Explorer
7. Question Detail
8. Review Center
9. Chapters & Topics
10. Practice
11. Practice Session
12. Practice Results
13. Analytics
14. Search
15. Settings
16. First Run

Additional design areas include the visual asset library, UI state library, reusable stat cards, and ModuleIQ design tokens.

Figma is not to be reverse-engineered from backend/database structure. New screens extend the established design language.

A live Figma MCP metadata refresh was attempted during this phase but was blocked by the current Figma MCP Starter-plan tool-call limit. This does not invalidate the existing design lock; Phase 3 will perform the live design-to-code verification before implementation of screens.

## 10. Major architectural risks identified

1. **Android/Termux native dependency pressure:** MinerU has heavy optional Torch/VLM/native dependencies. Phase 22/23 must validate the exact Android/Termux execution path rather than assuming every upstream runtime is equally portable.
2. **Framework boundary:** FastAPI and Huey should remain infrastructure dependencies/framework layers, while ModuleIQ owns domain logic.
3. **MinerU coupling:** ModuleIQ needs a canonical normalization interface so internal MinerU changes do not leak into every application feature.
4. **AI provider separation:** AI calls must produce validated ModuleIQ objects and must never become the primary persistence mechanism.
5. **License/attribution:** MinerU attribution and all supplied-source notices must survive the final product.
6. **Large-document processing:** ingestion must be asynchronous and checkpointed, not performed inside a browser request.
7. **Frontend/backend separation:** the Figma-designed experience must remain stable while backend implementation evolves.

## 11. Phase 0 reuse matrix

| Requirement | Supplied foundation | ModuleIQ work |
|---|---|---|
| PDF parsing | MinerU | Integration + normalization |
| OCR | MinerU | Pipeline integration + verification |
| Layout | MinerU | Pipeline integration |
| Equations | MinerU | Canonical storage + KaTeX rendering |
| Tables | MinerU | Canonical structured objects |
| Diagrams/figures | MinerU | Asset/provenance model |
| Document search | MinerU doclib/FTS | Extend to ModuleIQ knowledge search |
| Background processing | Huey + MinerU workers | ModuleIQ job orchestration |
| HTTP API | FastAPI | ModuleIQ domain API |
| Math rendering | KaTeX | Frontend integration |
| Knowledge model | None sufficient | Build |
| Question intelligence | Partial extraction foundation | Build |
| Adaptive learning | None sufficient | Build |
| BYOK | Partial provider/runtime primitives | Build |
| BYOM | Extraction foundation | Build |
| Practice/review/analytics | None sufficient | Build |
| Figma UI | Existing design | Implement exactly/extend consistently |

## 12. Architecture lock

The architecture is now locked as:

Material
→ validation
→ processing job
→ MinerU extraction
→ ModuleIQ normalization
→ persistent structured database
→ AI enrichment
→ verification/provenance
→ knowledge base
→ search/practice/review/analytics

AI remains a replaceable service layer.

## 13. Phase 0 gate

**GREEN**

All required Phase 0 findings are recorded:

- repository confirmed,
- supplied codebases inventoried,
- reusable capabilities identified,
- integration boundaries defined,
- license/attribution requirements identified,
- architecture risks identified,
- static syntax/integrity checks passed,
- Figma design lock confirmed from the existing inspected design baseline.

Next phase: **Phase 1 — Repository Foundation**.
