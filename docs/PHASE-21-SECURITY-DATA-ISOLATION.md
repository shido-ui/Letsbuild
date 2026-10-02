# Phase 21 — Security / Data Isolation

## Local-first security boundary

ModuleIQ remains single-user/local-first in this phase. It does not invent an authentication system; instead, API object access is constrained to the canonical local principal (local@moduleiq) and that user's workspace.

Protected boundaries include knowledge bases, AI providers, practice sessions, and review items. Analytics events no longer accept an arbitrary caller-supplied user ID.

## Transport/application hardening

The API adds baseline browser security headers and preserves explicit development CORS origins. Provider credentials remain encrypted and are never returned; only fingerprints are exposed.

## Non-goals

Full multi-user authentication, remote account management, and network deployment policy remain outside this phase and can be introduced when the deployment architecture requires them.
