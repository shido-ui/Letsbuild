# Phase 11 — Difficulty, Confidence & Verification

## Scope
Phase 11 makes AI-derived assessment explicit and inspectable.

Implemented:
- Multi-dimensional difficulty.
- Assessment confidence with provider/model/attempt/source-reference metadata.
- Question verification against normalized question context and available solutions.
- Verification status: verified, uncertain, failed.
- Solution confidence and verification linkage.
- Review Center routing for low-confidence assessment, uncertain/failed verification, and missing solutions.

## Design rule
AI-derived assessment is enrichment. The question, source provenance, and normalized database objects remain canonical.

## Gate validation
- Boundary/ambiguous questions: represented by confidence and verification status.
- Low-confidence classification: existing classification confidence participates in assessment confidence when present.
- Incorrect AI result: verification can produce failed.
- Verification failure: creates an open ReviewItem.
- Review routing: low-confidence and unresolved verification create open review items.

## Threshold
0.65 is the current review-routing threshold and is centralized for later tuning.

## Endpoint
POST /api/verification/questions/{question_id}?provider_id=<provider>
