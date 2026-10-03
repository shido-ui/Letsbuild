from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.models import (
    AIProvider, Block, Document, DocumentVersion, KnowledgeBase, LearnerProfile,
    Material, Page, PracticeSession, ProcessingJob, Question, ReviewItem,
    User, Workspace,
)

LOCAL_EMAIL="local@moduleiq"


def local_user(db:Session)->User|None:
    user=db.scalar(select(User).where(User.email==LOCAL_EMAIL))
    if user is not None:
        return user
    users=db.scalars(select(User).order_by(User.created_at)).all()
    return users[0] if len(users)==1 else None


def _owner_id(db:Session)->str:
    user=local_user(db)
    if user is None:
        raise ValueError("Local user not found")
    return user.id


def require_local_kb(db:Session,knowledge_base_id:str)->KnowledgeBase:
    owner=_owner_id(db)
    kb=db.scalar(
        select(KnowledgeBase)
        .join(Workspace,KnowledgeBase.workspace_id==Workspace.id)
        .where(KnowledgeBase.id==knowledge_base_id,Workspace.owner_id==owner)
    )
    if kb is None: raise ValueError("Knowledge base not found")
    return kb


def require_local_provider(db:Session,provider_id:str)->AIProvider:
    owner=_owner_id(db)
    provider=db.scalar(select(AIProvider).where(AIProvider.id==provider_id,AIProvider.user_id==owner))
    if provider is None: raise ValueError("Provider not found")
    return provider


def require_local_session(db:Session,session_id:str)->PracticeSession:
    owner=_owner_id(db)
    session=db.scalar(
        select(PracticeSession)
        .join(KnowledgeBase,PracticeSession.knowledge_base_id==KnowledgeBase.id)
        .join(Workspace,KnowledgeBase.workspace_id==Workspace.id)
        .where(PracticeSession.id==session_id,Workspace.owner_id==owner)
    )
    if session is None: raise ValueError("Practice session not found")
    return session


def require_local_review(db:Session,item_id:str)->ReviewItem:
    owner=_owner_id(db)
    item=db.scalar(
        select(ReviewItem)
        .join(KnowledgeBase,ReviewItem.knowledge_base_id==KnowledgeBase.id)
        .join(Workspace,KnowledgeBase.workspace_id==Workspace.id)
        .where(ReviewItem.id==item_id,Workspace.owner_id==owner)
    )
    if item is None: raise ValueError("Review item not found")
    return item


def require_local_profile(db:Session,profile_id:str)->LearnerProfile:
    owner=_owner_id(db)
    profile=db.scalar(select(LearnerProfile).where(LearnerProfile.id==profile_id,LearnerProfile.user_id==owner))
    if profile is None: raise ValueError("Learner profile not found")
    return profile


def require_local_question(db:Session,question_id:str)->Question:
    owner=_owner_id(db)
    question=db.scalar(
        select(Question)
        .join(KnowledgeBase,Question.knowledge_base_id==KnowledgeBase.id)
        .join(Workspace,KnowledgeBase.workspace_id==Workspace.id)
        .where(Question.id==question_id,Workspace.owner_id==owner)
    )
    if question is None: raise ValueError("Question not found")
    return question


def require_local_version(db:Session,version_id:str)->DocumentVersion:
    owner=_owner_id(db)
    version=db.scalar(
        select(DocumentVersion)
        .join(Document,DocumentVersion.document_id==Document.id)
        .join(Material,Document.material_id==Material.id)
        .join(KnowledgeBase,Material.knowledge_base_id==KnowledgeBase.id)
        .join(Workspace,KnowledgeBase.workspace_id==Workspace.id)
        .where(DocumentVersion.id==version_id,Workspace.owner_id==owner)
    )
    if version is None: raise ValueError("Document version not found")
    return version


def require_local_job(db:Session,job_id:str)->ProcessingJob:
    owner=_owner_id(db)
    job=db.scalar(
        select(ProcessingJob)
        .join(DocumentVersion,ProcessingJob.document_version_id==DocumentVersion.id)
        .join(Document,DocumentVersion.document_id==Document.id)
        .join(Material,Document.material_id==Material.id)
        .join(KnowledgeBase,Material.knowledge_base_id==KnowledgeBase.id)
        .join(Workspace,KnowledgeBase.workspace_id==Workspace.id)
        .where(ProcessingJob.id==job_id,Workspace.owner_id==owner)
    )
    if job is None: raise ValueError("Processing job not found")
    return job


def require_local_material(db:Session,material_id:str)->Material:
    owner=_owner_id(db)
    material=db.scalar(
        select(Material)
        .join(KnowledgeBase,Material.knowledge_base_id==KnowledgeBase.id)
        .join(Workspace,KnowledgeBase.workspace_id==Workspace.id)
        .where(Material.id==material_id,Workspace.owner_id==owner)
    )
    if material is None: raise ValueError("Material not found")
    return material


def require_local_document(db:Session,document_id:str)->Document:
    owner=_owner_id(db)
    document=db.scalar(
        select(Document)
        .join(Material,Document.material_id==Material.id)
        .join(KnowledgeBase,Material.knowledge_base_id==KnowledgeBase.id)
        .join(Workspace,KnowledgeBase.workspace_id==Workspace.id)
        .where(Document.id==document_id,Workspace.owner_id==owner)
    )
    if document is None: raise ValueError("Document not found")
    return document


def require_local_page(db:Session,page_id:str)->Page:
    owner=_owner_id(db)
    page=db.scalar(
        select(Page)
        .join(DocumentVersion,Page.document_version_id==DocumentVersion.id)
        .join(Document,DocumentVersion.document_id==Document.id)
        .join(Material,Document.material_id==Material.id)
        .join(KnowledgeBase,Material.knowledge_base_id==KnowledgeBase.id)
        .join(Workspace,KnowledgeBase.workspace_id==Workspace.id)
        .where(Page.id==page_id,Workspace.owner_id==owner)
    )
    if page is None: raise ValueError("Page not found")
    return page


def require_local_block(db:Session,block_id:str)->Block:
    owner=_owner_id(db)
    block=db.scalar(
        select(Block)
        .join(Page,Block.page_id==Page.id)
        .join(DocumentVersion,Page.document_version_id==DocumentVersion.id)
        .join(Document,DocumentVersion.document_id==Document.id)
        .join(Material,Document.material_id==Material.id)
        .join(KnowledgeBase,Material.knowledge_base_id==KnowledgeBase.id)
        .join(Workspace,KnowledgeBase.workspace_id==Workspace.id)
        .where(Block.id==block_id,Workspace.owner_id==owner)
    )
    if block is None: raise ValueError("Block not found")
    return block
