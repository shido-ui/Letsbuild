from __future__ import annotations

from contextvars import ContextVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.models import (
    AIProvider, Document, DocumentVersion, KnowledgeBase, LearnerProfile,
    Material, PracticeSession, ProcessingJob, Question, ReviewItem, User, Workspace,
)

LOCAL_EMAIL = "local@moduleiq"
_authenticated_user_id: ContextVar[str | None] = ContextVar("moduleiq_authenticated_user_id", default=None)


def set_authenticated_user(user_id: str) -> None:
    _authenticated_user_id.set(user_id)


def authenticated_user_id() -> str | None:
    return _authenticated_user_id.get()


def local_user(db: Session) -> User | None:
    user_id = authenticated_user_id()
    if user_id:
        return db.get(User, user_id)
    return db.scalar(select(User).where(User.email == LOCAL_EMAIL))

