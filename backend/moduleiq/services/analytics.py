from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.models import (
    AnalyticsEvent,
    KnowledgeBase,
    LearnerProfile,
    PracticeAttempt,
    PracticeSession,
    Question,
    Topic,
    TopicMastery,
)


def _assert_kb(db: Session, knowledge_base_id: str) -> None:
    if not db.get(KnowledgeBase, knowledge_base_id):
        raise ValueError("Knowledge base not found")


def log_event(
    db: Session,
    event_type: str,
    *,
    user_id: str | None = None,
    knowledge_base_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    occurred_at: datetime | None = None,
) -> dict[str, Any]:
    if knowledge_base_id:
        _assert_kb(db, knowledge_base_id)
    event = AnalyticsEvent(
        id=str(uuid4()),
        user_id=user_id,
        knowledge_base_id=knowledge_base_id,
        event_type=event_type.strip(),
        metadata_json=metadata or {},
        occurred_at=occurred_at or datetime.now().astimezone(),
    )
    db.add(event)
    db.flush()
    return {
        "id": event.id,
        "event_type": event.event_type,
        "knowledge_base_id": event.knowledge_base_id,
        "metadata": event.metadata_json or {},
        "occurred_at": event.occurred_at.isoformat(),
    }


def _day(value: datetime) -> str:
    return value.astimezone().date().isoformat()


def get_summary(db: Session, knowledge_base_id: str, *, days: int = 30) -> dict[str, Any]:
    _assert_kb(db, knowledge_base_id)
    days = max(1, min(days, 365))
    sessions = db.scalars(
        select(PracticeSession)
        .where(PracticeSession.knowledge_base_id == knowledge_base_id)
        .order_by(PracticeSession.started_at)
    ).all()
    session_ids = [s.id for s in sessions]
    attempts = (
        db.scalars(select(PracticeAttempt).where(PracticeAttempt.session_id.in_(session_ids))).all()
        if session_ids
        else []
    )

    answered = [a for a in attempts if not a.skipped]
    correct = [a for a in answered if a.is_correct is True]
    accuracy = round((len(correct) / len(answered)) * 100, 1) if answered else 0.0
    durations = [a.time_ms for a in answered if a.time_ms is not None]
    avg_time_ms = round(sum(durations) / len(durations)) if durations else None

    profile_ids = list(
        db.scalars(
            select(LearnerProfile.id)
            .join(PracticeSession, PracticeSession.learner_profile_id == LearnerProfile.id)
            .where(PracticeSession.knowledge_base_id == knowledge_base_id)
        ).all()
    )
    mastery_rows = (
        db.scalars(select(TopicMastery).where(TopicMastery.learner_profile_id.in_(profile_ids))).all()
        if profile_ids
        else []
    )
    topic_ids = [m.topic_id for m in mastery_rows]
    topics = (
        {t.id: t for t in db.scalars(select(Topic).where(Topic.id.in_(topic_ids))).all()}
        if topic_ids
        else {}
    )
    weak = sorted(
        [
            {"topic_id": m.topic_id, "topic": topics[m.topic_id].name, "mastery": round(m.mastery * 100, 1), "confidence": round(m.confidence * 100, 1)}
            for m in mastery_rows
            if m.topic_id in topics
        ],
        key=lambda x: (x["mastery"], x["topic"]),
    )[:8]
    overall_mastery = round(
        sum(m.mastery for m in mastery_rows) / len(mastery_rows) * 100, 1
    ) if mastery_rows else 0.0

    today = datetime.now().astimezone().date()
    cutoff = today - timedelta(days=days - 1)
    daily: dict[str, dict[str, int]] = defaultdict(lambda: {"answered": 0, "correct": 0, "sessions": 0})
    for s in sessions:
        d = _day(s.started_at)
        if d >= cutoff.isoformat():
            daily[d]["sessions"] += 1
    for a in attempts:
        created = a.created_at
        d = _day(created)
        if d >= cutoff.isoformat() and not a.skipped:
            daily[d]["answered"] += 1
            daily[d]["correct"] += int(a.is_correct is True)

    trend = []
    for offset in range(days):
        d = (cutoff + timedelta(days=offset)).isoformat()
        row = daily[d]
        trend.append({
            "date": d,
            "sessions": row["sessions"],
            "answered": row["answered"],
            "accuracy": round(row["correct"] / row["answered"] * 100, 1) if row["answered"] else None,
        })

    events = db.scalars(
        select(AnalyticsEvent)
        .where(AnalyticsEvent.knowledge_base_id == knowledge_base_id)
        .order_by(AnalyticsEvent.occurred_at.desc())
        .limit(100)
    ).all()

    return {
        "knowledge_base_id": knowledge_base_id,
        "window_days": days,
        "overall_mastery": overall_mastery,
        "accuracy": accuracy,
        "sessions": len(sessions),
        "questions_answered": len(answered),
        "questions_correct": len(correct),
        "questions_skipped": sum(1 for a in attempts if a.skipped),
        "avg_time_ms": avg_time_ms,
        "active_topics": len(mastery_rows),
        "weak_topics": weak,
        "trend": trend,
        "recent_events": [
            {"event_type": e.event_type, "occurred_at": e.occurred_at.isoformat(), "metadata": e.metadata_json or {}}
            for e in events
        ],
    }


def list_events(db: Session, knowledge_base_id: str, *, limit: int = 100) -> list[dict[str, Any]]:
    _assert_kb(db, knowledge_base_id)
    limit = max(1, min(limit, 500))
    rows = db.scalars(
        select(AnalyticsEvent)
        .where(AnalyticsEvent.knowledge_base_id == knowledge_base_id)
        .order_by(AnalyticsEvent.occurred_at.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "occurred_at": e.occurred_at.isoformat(),
            "metadata": e.metadata_json or {},
        }
        for e in rows
    ]
