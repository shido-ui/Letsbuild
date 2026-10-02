from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.session import get_db
from moduleiq.core.security import require_local_kb, require_local_session
from moduleiq.services.practice import (
    attempt,
    create_session,
    finish_session,
    get_results,
    get_session,
    pause_session,
    resume_session,
)

router = APIRouter(prefix="/practice", tags=["practice"])


class CreatePracticeRequest(BaseModel):
    knowledge_base_id: str
    mode: str = "fast"
    limit: int = Field(default=10, ge=1, le=100)
    topic_id: str | None = None
    difficulty: str | None = None
    question_type: str | None = None
    learner_profile_id: str | None = None


class AttemptRequest(BaseModel):
    question_id: str
    answer_text: str | None = None
    skipped: bool = False
    time_ms: int | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)


def _error(exc: ValueError) -> HTTPException:
    message = str(exc)
    return HTTPException(404 if "not found" in message.lower() else 400, message)


@router.post("/sessions")
def create(request: CreatePracticeRequest, db: Session = Depends(get_db)):
    try:
        return create_session(
            db,
            request.knowledge_base_id,
            mode=request.mode,
            limit=request.limit,
            topic_id=request.topic_id,
            difficulty=request.difficulty,
            question_type=request.question_type,
            learner_profile_id=request.learner_profile_id,
        )
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/sessions/{session_id}")
def read(session_id: str, db: Session = Depends(get_db)):
    try:
        return get_session(db, session_id)
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/sessions/{session_id}/attempt")
def submit(session_id: str, request: AttemptRequest, db: Session = Depends(get_db)):
    try:
        return attempt(
            db,
            session_id,
            question_id=request.question_id,
            answer_text=request.answer_text,
            skipped=request.skipped,
            time_ms=request.time_ms,
            confidence=request.confidence,
        )
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/sessions/{session_id}/pause")
def pause(session_id: str, db: Session = Depends(get_db)):
    try:
        return pause_session(db, session_id)
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/sessions/{session_id}/resume")
def resume(session_id: str, db: Session = Depends(get_db)):
    try:
        return resume_session(db, session_id)
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/sessions/{session_id}/finish")
def finish(session_id: str, db: Session = Depends(get_db)):
    try:
        return finish_session(db, session_id)
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/sessions/{session_id}/results")
def results(session_id: str, db: Session = Depends(get_db)):
    try:
        return get_results(db, session_id)
    except ValueError as exc:
        raise _error(exc) from exc
