# Phase 12 — Solution Engine

## Goal
Provide distinct source and AI solutions with provenance and verification.

## Implemented
- Source-answer extraction from labelled solution/answer blocks when present.
- Persistent SourceSolution records with source-page and source-block provenance.
- Provider-layer AI solution generation.
- Step-by-step solution metadata.
- Equation, table and diagram context from the source page.
- AI verification persisted on the AI solution.
- Confidence/provider/model metadata.
- Separate solution retrieval and generation endpoints.
- Frontend-ready distinction between source and AI solution types.

## Gate
A question exposes original source material separately from AI-generated explanation; AI generation and verification remain replaceable provider operations, and generation failure does not mutate the canonical question.
