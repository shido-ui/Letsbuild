from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.models import AIProvider, KnowledgeBase, LearnerProfile, PracticeSession, ReviewItem, User, Workspace
LOCAL_EMAIL = "local@moduleiq"

def local_user(db: Session) -> User | None:
    return db.scalar(select(User).where(User.email == LOCAL_EMAIL))

def require_local_kb(db: Session, knowledge_base_id: str) -> KnowledgeBase:
    kb = db.scalar(select(KnowledgeBase).join(Workspace, KnowledgeBase.workspace_id == Workspace.id).join(User, Workspace.owner_id == User.id).where(KnowledgeBase.id == knowledge_base_id, User.email == LOCAL_EMAIL))
    if kb is None: raise ValueError("Knowledge base not found")
    return kb

def require_local_provider(db: Session, provider_id: str) -> AIProvider:
    provider = db.scalar(select(AIProvider).join(User, AIProvider.user_id == User.id).where(AIProvider.id == provider_id, User.email == LOCAL_EMAIL))
    if provider is None: raise ValueError("Provider not found")
    return provider

def require_local_session(db: Session, session_id: str) -> PracticeSession:
    session = db.scalar(select(PracticeSession).join(KnowledgeBase, PracticeSession.knowledge_base_id == KnowledgeBase.id).join(Workspace, KnowledgeBase.workspace_id == Workspace.id).join(User, Workspace.owner_id == User.id).where(PracticeSession.id == session_id, User.email == LOCAL_EMAIL))
    if session is None: raise ValueError("Practice session not found")
    return session

def require_local_review(db: Session, item_id: str) -> ReviewItem:
    item = db.scalar(select(ReviewItem).join(KnowledgeBase, ReviewItem.knowledge_base_id == KnowledgeBase.id).join(Workspace, KnowledgeBase.workspace_id == Workspace.id).join(User, Workspace.owner_id == User.id).where(ReviewItem.id == item_id, User.email == LOCAL_EMAIL))
    if item is None: raise ValueError("Review item not found")
    return item


def require_local_profile(db: Session, profile_id: str) -> LearnerProfile:
    profile = db.scalar(select(LearnerProfile).join(User, LearnerProfile.user_id == User.id).where(LearnerProfile.id == profile_id, User.email == LOCAL_EMAIL))
    if profile is None: raise ValueError("Learner profile not found")
    return profile
