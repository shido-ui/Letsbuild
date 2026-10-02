from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from moduleiq.core.security import local_user, require_local_kb
from moduleiq.infrastructure.database.session import get_db
from moduleiq.services.analytics import get_summary, list_events, log_event

router = APIRouter(prefix="/analytics", tags=["analytics"])


class EventRequest(BaseModel):
    event_type: str = Field(min_length=1, max_length=100)
    knowledge_base_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime | None = None


def _error(exc: ValueError) -> HTTPException:
    return HTTPException(
        status_code=404 if "not found" in str(exc).lower() else 400,
        detail=str(exc),
    )


@router.get("/summary")
def summary(
    knowledge_base_id: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    try:
        require_local_kb(db, knowledge_base_id)
        return get_summary(db, knowledge_base_id, days=days)
    except ValueError as exc:
        raise _error(exc) from exc


@router.get("/events")
def events(
    knowledge_base_id: str,
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    try:
        require_local_kb(db, knowledge_base_id)
        return {"events": list_events(db, knowledge_base_id, limit=limit)}
    except ValueError as exc:
        raise _error(exc) from exc


@router.post("/events")
def create_event(request: EventRequest, db: Session = Depends(get_db)):
    try:
        user = local_user(db)
        if user is None:
            raise ValueError("Local user not found")
        if request.knowledge_base_id:
            require_local_kb(db, request.knowledge_base_id)
        result = log_event(
            db,
            request.event_type,
            user_id=user.id,
            knowledge_base_id=request.knowledge_base_id,
            metadata=request.metadata,
            occurred_at=request.occurred_at,
        )
        db.commit()
        return result
    except ValueError as exc:
        db.rollback()
        raise _error(exc) from exc
