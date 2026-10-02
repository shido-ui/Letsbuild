# Phase 18 — Analytics

Phase 18 replaces the decorative Analytics screen with persisted product telemetry and learning metrics.

## Delivered

- Added `services/analytics.py` for canonical analytics events and knowledge-base-scoped summaries.
- Added `GET /api/analytics/summary` with 1–365 day windows.
- Added `GET /api/analytics/events` for persisted event history.
- Added `POST /api/analytics/events` for explicit event ingestion.
- Analytics summary derives practice accuracy, answered/correct/skipped counts, average answer time, session count, active adaptive topics, overall mastery, weak topics, daily practice trend, and recent events from persisted data.
- Practice sessions and attempts now emit persisted analytics events when a learner profile is attached.
- Replaced the Analytics frontend placeholders with live API data, time-window controls, mastery/accuracy metrics, practice trend, weak topics, timing, and recent activity.
- Added self-contained analytics persistence tests.
- Added a dedicated Phase 18 CI gate running compile, migrations, and the complete backend test suite.

## Source of truth

Analytics is observational data over the canonical database. It does not replace knowledge objects, practice records, or adaptive mastery state.

## Verification

The Phase 18 workflow must remain green before advancing to Phase 19.
