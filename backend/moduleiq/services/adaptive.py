from __future__ import annotations

from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.models import (
    Concept,
    DifficultyAssessment,
    LearnerProfile,
    PracticeAttempt,
    PracticeSession,
    Question,
    Topic,
    TopicMastery,
)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def get_or_create_profile(db: Session, user_id: str) -> LearnerProfile:
    profile = db.scalar(select(LearnerProfile).where(LearnerProfile.user_id == user_id))
    if profile:
        return profile
    profile = LearnerProfile(id=str(uuid4()), user_id=user_id)
    db.add(profile)
    db.flush()
    return profile


def _topic_from_question(db: Session, question: Question) -> Topic | None:
    if not question.classification_id:
        return None
    from moduleiq.infrastructure.database.models import Classification
    classification = db.get(Classification, question.classification_id)
    if not classification or not classification.topic:
        return None
    return db.scalar(select(Topic).where(Topic.name == classification.topic))


def update_from_attempt(db: Session, attempt: PracticeAttempt) -> dict[str, Any] | None:
    session = db.get(PracticeSession, attempt.session_id)
    if not session or not session.learner_profile_id:
        return None
    question = db.get(Question, attempt.question_id)
    if not question:
        return None
    topic = _topic_from_question(db, question)
    if not topic:
        return None

    mastery = db.scalar(
        select(TopicMastery).where(
            TopicMastery.learner_profile_id == session.learner_profile_id,
            TopicMastery.topic_id == topic.id,
        )
    )
    if not mastery:
        mastery = TopicMastery(
            id=str(uuid4()),
            learner_profile_id=session.learner_profile_id,
            topic_id=topic.id,
            mastery=0.0,
            confidence=0.0,
        )
        db.add(mastery)
        db.flush()

    # Small, bounded Bayesian-like update: correct answers raise mastery,
    # incorrect/skipped answers lower it, with diminishing step size.
    prior = mastery.mastery
    evidence = 0.05 if attempt.skipped else (0.12 if attempt.is_correct else -0.10)
    weight = max(0.25, 1.0 - prior * 0.6)
    mastery.mastery = round(_clamp(prior + evidence * weight), 4)
    mastery.confidence = round(_clamp(mastery.confidence + (0.08 if attempt.is_correct else 0.04)), 4)
    mastery.metadata_json = {
        **(mastery.metadata_json or {}),
        "last_question_id": question.id,
        "attempt_count": int((mastery.metadata_json or {}).get("attempt_count", 0)) + 1,
    }
    db.flush()
    return {"topic_id": topic.id, "topic": topic.name, "mastery": mastery.mastery, "confidence": mastery.confidence}


def mastery(db: Session, learner_profile_id: str, knowledge_base_id: str) -> list[dict[str, Any]]:
    rows = db.execute(
        select(TopicMastery, Topic)
        .join(Topic, Topic.id == TopicMastery.topic_id)
        .where(TopicMastery.learner_profile_id == learner_profile_id)
        .order_by(TopicMastery.mastery.asc(), Topic.name.asc())
    ).all()
    return [
        {
            "topic_id": topic.id,
            "topic": topic.name,
            "mastery": row.mastery,
            "confidence": row.confidence,
            "needs_review": row.mastery < 0.6 or row.confidence < 0.4,
        }
        for row, topic in rows
    ]


def recommendations(db: Session, learner_profile_id: str, knowledge_base_id: str, limit: int = 10) -> list[dict[str, Any]]:
    weak = mastery(db, learner_profile_id, knowledge_base_id)
    weak_topics = {x["topic_id"]: x for x in weak if x["needs_review"]}
    questions = db.scalars(
        select(Question).where(Question.knowledge_base_id == knowledge_base_id).limit(500)
    ).all()
    ranked: list[tuple[float, Question, dict[str, Any] | None]] = []
    for question in questions:
        topic = _topic_from_question(db, question)
        if not topic or topic.id not in weak_topics:
            continue
        difficulty = db.get(DifficultyAssessment, question.difficulty_id) if question.difficulty_id else None
        d = difficulty.overall if difficulty else 0.5
        target = weak_topics[topic.id]["mastery"]
        # Prefer questions near the learner's current mastery and weak topics.
        fit = 1.0 - abs((d or 0.5) - (target or 0.5))
        ranked.append((weak_topics[topic.id]["mastery"] + fit * 0.1, question, weak_topics[topic.id]))
    ranked.sort(key=lambda x: x[0])
    return [
        {
            "question_id": q.id,
            "text": q.text,
            "topic_id": t["topic_id"],
            "topic": t["topic"],
            "mastery": t["mastery"],
            "reason": "weak_topic",
        }
        for _, q, t in ranked[: max(1, min(limit, 50))]
    ]
