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


def require_local_kb(db: Session, knowledge_base_id: str) -> KnowledgeBase:
    kb = db.scalar(
        select(KnowledgeBase)
        .join(Workspace, KnowledgeBase.workspace_id == Workspace.id)
        .join(User, Workspace.owner_id == User.id)
        .where(KnowledgeBase.id == knowledge_base_id, User.id == _owner_id(db))
    )
    if kb is None:
        raise ValueError("Knowledge base not found")
    return kb


def _owner_id(db: Session) -> str:
    user_id = authenticated_user_id()
    if user_id:
        return user_id
    user = db.scalar(select(User).where(User.email == LOCAL_EMAIL))
    if user is None:
        raise ValueError("Local user not found")
    return user.id


def require_local_provider(db: Session, provider_id: str) -> AIProvider:
    provider = db.scalar(
        select(AIProvider)
        .join(User, AIProvider.user_id == User.id)
        .where(AIProvider.id == provider_id, User.id == _owner_id(db))
    )
    if provider is None:
        raise ValueError("Provider not found")
    return provider


def require_local_session(db: Session, session_id: str) -> PracticeSession:
    session = db.scalar(
        select(PracticeSession)
        .join(KnowledgeBase, PracticeSession.knowledge_base_id == KnowledgeBase.id)
        .join(Workspace, KnowledgeBase.workspace_id == Workspace.id)
        .join(User, Workspace.owner_id == User.id)
        .where(PracticeSession.id == session_id, User.id == _owner_id(db))
    )
    if session is None:
        raise ValueError("Practice session not found")
    return session


def require_local_review(db: Session, item_id: str) -> ReviewItem:
    item = db.scalar(
        select(ReviewItem)
        .join(KnowledgeBase, ReviewItem.knowledge_base_id == KnowledgeBase.id)
        .join(Workspace, KnowledgeBase.workspace_id == Workspace.id)
        .join(User, Workspace.owner_id == User.id)
        .where(ReviewItem.id == item_id, User.id == _owner_id(db))
    )
    if item is None:
        raise ValueError("Review item not found")
    return item


def require_local_profile(db: Session, profile_id: str) -> LearnerProfile:
    profile = db.scalar(
        select(LearnerProfile)
        .join(User, LearnerProfile.user_id == User.id)
        .where(LearnerProfile.id == profile_id, User.id == _owner_id(db))
    )
    if profile is None:
        raise ValueError("Learner profile not found")
    return profile


def require_local_question(db: Session, question_id: str) -> Question:
    question = db.scalar(
        select(Question)
        .join(KnowledgeBase, Question.knowledge_base_id == KnowledgeBase.id)
        .join(Workspace, KnowledgeBase.workspace_id == Workspace.id)
        .join(User, Workspace.owner_id == User.id)
        .where(Question.id == question_id, User.id == _owner_id(db))
    )
    if question is None:
        raise ValueError("Question not found")
    return question


def require_local_version(db: Session, version_id: str) -> DocumentVersion:
    version = db.scalar(
        select(DocumentVersion)
        .join(Document, DocumentVersion.document_id == Document.id)
        .join(Material, Document.material_id == Material.id)
        .join(KnowledgeBase, Material.knowledge_base_id == KnowledgeBase.id)
        .join(Workspace, KnowledgeBase.workspace_id == Workspace.id)
        .join(User, Workspace.owner_id == User.id)
        .where(DocumentVersion.id == version_id, User.id == _owner_id(db))
    )
    if version is None:
        raise ValueError("Document version not found")
    return version


def require_local_job(db: Session, job_id: str) -> ProcessingJob:
    job = db.scalar(
        select(ProcessingJob)
        .join(DocumentVersion, ProcessingJob.document_version_id == DocumentVersion.id)
        .join(Document, DocumentVersion.document_id == Document.id)
        .join(Material, Document.material_id == Material.id)
        .join(KnowledgeBase, Material.knowledge_base_id == KnowledgeBase.id)
        .join(Workspace, KnowledgeBase.workspace_id == Workspace.id)
        .join(User, Workspace.owner_id == User.id)
        .where(ProcessingJob.id == job_id, User.id == _owner_id(db))
    )
    if job is None:
        raise ValueError("Processing job not found")
    return job
