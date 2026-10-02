from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.models import (
    DifficultyAssessment,
    PracticeAttempt,
    PracticeSession,
    Question,
    QuestionOption,
)

MODES = {"fast", "deep", "boss", "custom"}
ACTIVE_STATUSES = {"active", "paused"}


def _now() -> datetime:
    return datetime.now().astimezone()


def _question_payload(db: Session, question: Question) -> dict[str, Any]:
    options = db.scalars(
        select(QuestionOption)
        .where(QuestionOption.question_id == question.id)
        .order_by(QuestionOption.ordinal)
    ).all()
    difficulty = db.get(DifficultyAssessment, question.difficulty_id) if question.difficulty_id else None
    return {
        "id": question.id,
        "text": question.text,
        "question_type": question.question_type,
        "difficulty": difficulty.overall if difficulty else None,
        "options": [
            {"id": o.id, "ordinal": o.ordinal, "text": o.option_text}
            for o in options
        ],
    }


def _session_question_ids(session: PracticeSession) -> list[str]:
    return list((session.metadata_json or {}).get("question_ids", []))


def _state(session: PracticeSession) -> dict[str, Any]:
    return dict(session.metadata_json or {})


def _get_session(db: Session, session_id: str) -> PracticeSession:
    session = db.get(PracticeSession, session_id)
    if not session:
        raise ValueError("Practice session not found")
    return session


def _assert_kb(db: Session, knowledge_base_id: str) -> None:
    from moduleiq.infrastructure.database.models import KnowledgeBase
    if not db.get(KnowledgeBase, knowledge_base_id):
        raise ValueError("Knowledge base not found")


def create_session(
    db: Session,
    knowledge_base_id: str,
    *,
    mode: str = "fast",
    limit: int = 10,
    topic_id: str | None = None,
    difficulty: str | None = None,
    question_type: str | None = None,
    learner_profile_id: str | None = None,
) -> dict[str, Any]:
    if mode not in MODES:
        raise ValueError("Invalid practice mode")
    _assert_kb(db, knowledge_base_id)
    limit = max(1, min(limit, 100))

    stmt = select(Question).where(Question.knowledge_base_id == knowledge_base_id)
    if question_type:
        stmt = stmt.where(Question.question_type == question_type)
    if difficulty:
        stmt = stmt.join(DifficultyAssessment, Question.difficulty_id == DifficultyAssessment.id).where(
            DifficultyAssessment.overall >= float(difficulty),
            DifficultyAssessment.overall < float(difficulty) + 1,
        )
    # Topic filtering is resolved from the canonical classification when available.
    if topic_id:
        from moduleiq.infrastructure.database.models import Classification
        stmt = stmt.join(Classification, Question.classification_id == Classification.id).where(
            Classification.topic == topic_id
        )

    questions = db.scalars(stmt.order_by(Question.created_at, Question.id).limit(limit)).all()
    if not questions:
        raise ValueError("No practice questions match this configuration")

    ids = [q.id for q in questions]
    session = PracticeSession(
        id=str(uuid4()),
        knowledge_base_id=knowledge_base_id,
        mode=mode,
        status="active",
        metadata_json={
            "version": 1,
            "question_ids": ids,
            "current_index": 0,
            "limit": len(ids),
            "config": {
                "topic_id": topic_id,
                "difficulty": difficulty,
                "question_type": question_type,
            },
        },
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return get_session(db, session.id)


def get_session(db: Session, session_id: str) -> dict[str, Any]:
    session = _get_session(db, session_id)
    state = _state(session)
    ids = _session_question_ids(session)
    questions = {
        q.id: q for q in db.scalars(select(Question).where(Question.id.in_(ids))).all()
    }
    attempts = db.scalars(
        select(PracticeAttempt)
        .where(PracticeAttempt.session_id == session.id)
        .order_by(PracticeAttempt.created_at)
    ).all()
    current_index = int(state.get("current_index", 0))
    current_id = ids[current_index] if 0 <= current_index < len(ids) else None
    return {
        "id": session.id,
        "knowledge_base_id": session.knowledge_base_id,
        "mode": session.mode,
        "status": session.status,
        "started_at": session.started_at.isoformat() if session.started_at else None,
        "ended_at": session.ended_at.isoformat() if session.ended_at else None,
        "current_index": current_index,
        "total_questions": len(ids),
        "current_question": _question_payload(db, questions[current_id]) if current_id in questions else None,
        "questions": [_question_payload(db, questions[qid]) for qid in ids if qid in questions],
        "attempts": [
            {
                "id": a.id,
                "question_id": a.question_id,
                "answer_text": a.answer_text,
                "is_correct": a.is_correct,
                "skipped": a.skipped,
                "time_ms": a.time_ms,
                "confidence": a.confidence,
            }
            for a in attempts
        ],
        "config": state.get("config", {}),
    }


def attempt(
    db: Session,
    session_id: str,
    *,
    question_id: str,
    answer_text: str | None = None,
    skipped: bool = False,
    time_ms: int | None = None,
    confidence: float | None = None,
) -> dict[str, Any]:
    session = _get_session(db, session_id)
    if session.status not in ACTIVE_STATUSES:
        raise ValueError("Practice session is not active")
    ids = _session_question_ids(session)
    if question_id not in ids:
        raise ValueError("Question does not belong to this session")

    question = db.get(Question, question_id)
    if not question:
        raise ValueError("Question not found")

    existing = db.scalars(
        select(PracticeAttempt)
        .where(
            PracticeAttempt.session_id == session_id,
            PracticeAttempt.question_id == question_id,
        )
        .order_by(PracticeAttempt.created_at.desc())
    ).first()

    if existing:
        raise ValueError("Question has already been attempted in this session")

    is_correct: bool | None = None
    if not skipped and answer_text is not None:
        options = db.scalars(select(QuestionOption).where(QuestionOption.question_id == question_id)).all()
        if options:
            selected = answer_text.strip().lower()
            matching = next((o for o in options if o.id.lower() == selected or o.option_text.strip().lower() == selected), None)
            is_correct = bool(matching and matching.is_correct)
        else:
            is_correct = None

    new_attempt = PracticeAttempt(
            id=str(uuid4()),
            session_id=session_id,
            question_id=question_id,
            answer_text=answer_text,
            is_correct=is_correct,
            skipped=skipped,
            time_ms=max(0, time_ms) if time_ms is not None else None,
            confidence=confidence,
        )
    )
    db.add(new_attempt)
    if session.learner_profile_id:
        from moduleiq.services.adaptive import update_from_attempt
        update_from_attempt(db, new_attempt)

    state = _state(session)
    current_index = ids.index(question_id)
    state["current_index"] = min(current_index + 1, len(ids))
    session.metadata_json = state
    if state["current_index"] >= len(ids):
        session.status = "completed"
        session.ended_at = _now()
    db.commit()
    return get_session(db, session_id)


def pause_session(db: Session, session_id: str) -> dict[str, Any]:
    session = _get_session(db, session_id)
    if session.status != "active":
        raise ValueError("Only an active session can be paused")
    session.status = "paused"
    db.commit()
    return get_session(db, session_id)


def resume_session(db: Session, session_id: str) -> dict[str, Any]:
    session = _get_session(db, session_id)
    if session.status != "paused":
        raise ValueError("Only a paused session can be resumed")
    session.status = "active"
    db.commit()
    return get_session(db, session_id)


def finish_session(db: Session, session_id: str) -> dict[str, Any]:
    session = _get_session(db, session_id)
    if session.status == "completed":
        return get_results(db, session_id)
    if session.status not in ACTIVE_STATUSES:
        raise ValueError("Practice session cannot be finished")
    session.status = "completed"
    session.ended_at = _now()
    db.commit()
    return get_results(db, session_id)


def get_results(db: Session, session_id: str) -> dict[str, Any]:
    session = _get_session(db, session_id)
    attempts = db.scalars(select(PracticeAttempt).where(PracticeAttempt.session_id == session_id)).all()
    total = len(_session_question_ids(session))
    answered = [a for a in attempts if not a.skipped]
    correct = sum(1 for a in attempts if a.is_correct is True)
    skipped = sum(1 for a in attempts if a.skipped)
    attempted = len(attempts)
    score = round((correct / total) * 100, 2) if total else 0.0
    return {
        "session_id": session.id,
        "status": session.status,
        "mode": session.mode,
        "total_questions": total,
        "attempted": attempted,
        "answered": len(answered),
        "correct": correct,
        "skipped": skipped,
        "score": score,
        "duration_ms": max(0, int((session.ended_at - session.started_at).total_seconds() * 1000))
        if session.ended_at and session.started_at else None,
        "attempts": [
            {
                "question_id": a.question_id,
                "answer_text": a.answer_text,
                "is_correct": a.is_correct,
                "skipped": a.skipped,
                "time_ms": a.time_ms,
            }
            for a in attempts
        ],
    }
