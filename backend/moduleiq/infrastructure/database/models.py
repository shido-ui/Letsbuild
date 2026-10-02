from __future__ import annotations
from datetime import datetime
from typing import Any
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, IdMixin, JSONMixin, TimestampMixin, utc_now

class User(IdMixin, TimestampMixin, Base):
    __tablename__="users"
    email: Mapped[str]=mapped_column(String(320), unique=True, nullable=False, index=True)
    display_name: Mapped[str|None]=mapped_column(String(200))
    workspaces: Mapped[list["Workspace"]]=relationship(back_populates="owner", cascade="all, delete-orphan")

class Workspace(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="workspaces"
    owner_id: Mapped[str]=mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str]=mapped_column(String(200), nullable=False)
    owner: Mapped[User]=relationship(back_populates="workspaces")
    knowledge_bases: Mapped[list["KnowledgeBase"]]=relationship(back_populates="workspace", cascade="all, delete-orphan")

class KnowledgeBase(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="knowledge_bases"
    workspace_id: Mapped[str]=mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str]=mapped_column(String(200), nullable=False)
    description: Mapped[str|None]=mapped_column(Text)
    workspace: Mapped[Workspace]=relationship(back_populates="knowledge_bases")
    materials: Mapped[list["Material"]]=relationship(back_populates="knowledge_base", cascade="all, delete-orphan")

class Material(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="materials"
    knowledge_base_id: Mapped[str]=mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str]=mapped_column(String(500), nullable=False)
    media_type: Mapped[str]=mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int|None]=mapped_column(Integer)
    sha256: Mapped[str|None]=mapped_column(String(64), index=True)
    knowledge_base: Mapped[KnowledgeBase]=relationship(back_populates="materials")
    documents: Mapped[list["Document"]]=relationship(back_populates="material", cascade="all, delete-orphan")

class Document(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="documents"
    material_id: Mapped[str]=mapped_column(ForeignKey("materials.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str|None]=mapped_column(String(500))
    current_version_id: Mapped[str|None]=mapped_column(ForeignKey("document_versions.id", ondelete="SET NULL"))
    material: Mapped[Material]=relationship(back_populates="documents")
    versions: Mapped[list["DocumentVersion"]]=relationship(back_populates="document", cascade="all, delete-orphan", foreign_keys="DocumentVersion.document_id")
    current_version: Mapped["DocumentVersion|None"]=relationship(foreign_keys=[current_version_id], post_update=True)

class DocumentVersion(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="document_versions"
    document_id: Mapped[str]=mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number: Mapped[int]=mapped_column(Integer, nullable=False)
    storage_uri: Mapped[str|None]=mapped_column(String(2000))
    processing_status: Mapped[str]=mapped_column(String(40), default="pending", nullable=False, index=True)
    document: Mapped[Document]=relationship(back_populates="versions")
    pages: Mapped[list["Page"]]=relationship(back_populates="document_version", cascade="all, delete-orphan")
    __table_args__=(UniqueConstraint("document_id","version_number"),)

class Page(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="pages"
    document_version_id: Mapped[str]=mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    page_number: Mapped[int]=mapped_column(Integer, nullable=False)
    width: Mapped[float|None]=mapped_column(Float)
    height: Mapped[float|None]=mapped_column(Float)
    document_version: Mapped[DocumentVersion]=relationship(back_populates="pages")
    blocks: Mapped[list["Block"]]=relationship(back_populates="page", cascade="all, delete-orphan")
    __table_args__=(UniqueConstraint("document_version_id","page_number"),)

class Block(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="blocks"
    page_id: Mapped[str]=mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True)
    block_type: Mapped[str]=mapped_column(String(50), nullable=False, index=True)
    ordinal: Mapped[int]=mapped_column(Integer, nullable=False)
    text: Mapped[str|None]=mapped_column(Text)
    bbox_json: Mapped[dict[str,Any]|None]=mapped_column(__import__("sqlalchemy").JSON)
    page: Mapped[Page]=relationship(back_populates="blocks")

class Section(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="sections"
    parent_id: Mapped[str|None]=mapped_column(ForeignKey("sections.id", ondelete="CASCADE"), index=True)
    document_version_id: Mapped[str|None]=mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), index=True)
    title: Mapped[str]=mapped_column(String(500), nullable=False)
    level: Mapped[int]=mapped_column(Integer, default=1, nullable=False)
    parent: Mapped["Section|None"]=relationship(remote_side="Section.id", back_populates="children")
    children: Mapped[list["Section"]]=relationship(back_populates="parent", cascade="all, delete-orphan")
    chapters: Mapped[list["Chapter"]]=relationship(back_populates="section")

class Chapter(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="chapters"
    section_id: Mapped[str]=mapped_column(ForeignKey("sections.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str]=mapped_column(String(500), nullable=False)
    ordinal: Mapped[int]=mapped_column(Integer, nullable=False)
    section: Mapped[Section]=relationship(back_populates="chapters")
    topics: Mapped[list["Topic"]]=relationship(back_populates="chapter", cascade="all, delete-orphan")

class Topic(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="topics"
    chapter_id: Mapped[str|None]=mapped_column(ForeignKey("chapters.id", ondelete="CASCADE"), index=True)
    parent_id: Mapped[str|None]=mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), index=True)
    name: Mapped[str]=mapped_column(String(500), nullable=False)
    chapter: Mapped[Chapter|None]=relationship(back_populates="topics")
    parent: Mapped["Topic|None"]=relationship(remote_side="Topic.id", back_populates="children")
    children: Mapped[list["Topic"]]=relationship(back_populates="parent", cascade="all, delete-orphan")
    subtopics: Mapped[list["Subtopic"]]=relationship(back_populates="topic", cascade="all, delete-orphan")

class Subtopic(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="subtopics"
    topic_id: Mapped[str]=mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str]=mapped_column(String(500), nullable=False)
    topic: Mapped[Topic]=relationship(back_populates="subtopics")
    concepts: Mapped[list["Concept"]]=relationship(back_populates="subtopic", cascade="all, delete-orphan")

class Concept(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="concepts"
    subtopic_id: Mapped[str|None]=mapped_column(ForeignKey("subtopics.id", ondelete="CASCADE"), index=True)
    name: Mapped[str]=mapped_column(String(500), nullable=False)
    definition: Mapped[str|None]=mapped_column(Text)
    subtopic: Mapped[Subtopic|None]=relationship(back_populates="concepts")

class Equation(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="equations"
    page_id: Mapped[str|None]=mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), index=True)
    latex: Mapped[str]=mapped_column(Text, nullable=False)
    source_text: Mapped[str|None]=mapped_column(Text)

class Table(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="tables"
    page_id: Mapped[str|None]=mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), index=True)
    caption: Mapped[str|None]=mapped_column(Text)
    data_json: Mapped[list[list[Any]]]=mapped_column(__import__("sqlalchemy").JSON, nullable=False)

class Asset(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="assets"
    storage_uri: Mapped[str]=mapped_column(String(2000), nullable=False)
    media_type: Mapped[str]=mapped_column(String(100), nullable=False)
    sha256: Mapped[str|None]=mapped_column(String(64), index=True)
    byte_size: Mapped[int|None]=mapped_column(Integer)

class Diagram(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="diagrams"
    page_id: Mapped[str|None]=mapped_column(ForeignKey("pages.id", ondelete="CASCADE"), index=True)
    caption: Mapped[str|None]=mapped_column(Text)
    asset_id: Mapped[str|None]=mapped_column(ForeignKey("assets.id", ondelete="SET NULL"))

class Classification(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="classifications"
    subject: Mapped[str|None]=mapped_column(String(200))
    topic: Mapped[str|None]=mapped_column(String(500))
    subtopic: Mapped[str|None]=mapped_column(String(500))
    confidence: Mapped[float|None]=mapped_column(Float)

class DifficultyAssessment(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="difficulty_assessments"
    overall: Mapped[float|None]=mapped_column(Float)
    reasoning_depth: Mapped[float|None]=mapped_column(Float)
    calculation_complexity: Mapped[float|None]=mapped_column(Float)
    conceptual_complexity: Mapped[float|None]=mapped_column(Float)
    prerequisite_depth: Mapped[float|None]=mapped_column(Float)

class Verification(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="verifications"
    status: Mapped[str]=mapped_column(String(40), nullable=False, index=True)
    verifier_type: Mapped[str|None]=mapped_column(String(50))
    confidence: Mapped[float|None]=mapped_column(Float)
    notes: Mapped[str|None]=mapped_column(Text)

class Provenance(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="provenance"
    source_kind: Mapped[str]=mapped_column(String(30), nullable=False)
    source_document_id: Mapped[str|None]=mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), index=True)
    source_page_id: Mapped[str|None]=mapped_column(ForeignKey("pages.id", ondelete="SET NULL"))
    source_block_id: Mapped[str|None]=mapped_column(ForeignKey("blocks.id", ondelete="SET NULL"))
    locator: Mapped[str|None]=mapped_column(String(1000))
    confidence: Mapped[float|None]=mapped_column(Float)

class Question(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="questions"
    knowledge_base_id: Mapped[str]=mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    text: Mapped[str]=mapped_column(Text, nullable=False)
    question_type: Mapped[str]=mapped_column(String(50), nullable=False, index=True)
    difficulty_id: Mapped[str|None]=mapped_column(ForeignKey("difficulty_assessments.id", ondelete="SET NULL"))
    classification_id: Mapped[str|None]=mapped_column(ForeignKey("classifications.id", ondelete="SET NULL"))
    provenance_id: Mapped[str|None]=mapped_column(ForeignKey("provenance.id", ondelete="SET NULL"))
    options: Mapped[list["QuestionOption"]]=relationship(back_populates="question", cascade="all, delete-orphan")
    solutions: Mapped[list["QuestionSolution"]]=relationship(back_populates="question", cascade="all, delete-orphan")

class QuestionOption(IdMixin, TimestampMixin, Base):
    __tablename__="question_options"
    question_id: Mapped[str]=mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    ordinal: Mapped[int]=mapped_column(Integer, nullable=False)
    option_text: Mapped[str]=mapped_column(Text, nullable=False)
    is_correct: Mapped[bool|None]=mapped_column(Boolean)
    question: Mapped[Question]=relationship(back_populates="options")
    __table_args__=(UniqueConstraint("question_id","ordinal"),)

class QuestionSolution(IdMixin, TimestampMixin, Base):
    __tablename__="question_solutions"
    question_id: Mapped[str]=mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    solution_type: Mapped[str]=mapped_column(String(30), nullable=False)
    body: Mapped[str]=mapped_column(Text, nullable=False)
    confidence: Mapped[float|None]=mapped_column(Float)
    verification_id: Mapped[str|None]=mapped_column(ForeignKey("verifications.id", ondelete="SET NULL"))
    question: Mapped[Question]=relationship(back_populates="solutions")
    source_solution: Mapped["SourceSolution|None"]=relationship(back_populates="question_solution", uselist=False, cascade="all, delete-orphan")
    ai_solution: Mapped["AISolution|None"]=relationship(back_populates="question_solution", uselist=False, cascade="all, delete-orphan")

class SourceSolution(IdMixin, TimestampMixin, Base):
    __tablename__="source_solutions"
    question_solution_id: Mapped[str]=mapped_column(ForeignKey("question_solutions.id", ondelete="CASCADE"), unique=True, nullable=False)
    source_page_id: Mapped[str|None]=mapped_column(ForeignKey("pages.id", ondelete="SET NULL"))
    question_solution: Mapped[QuestionSolution]=relationship(back_populates="source_solution")

class AISolution(IdMixin, TimestampMixin, Base):
    __tablename__="ai_solutions"
    question_solution_id: Mapped[str]=mapped_column(ForeignKey("question_solutions.id", ondelete="CASCADE"), unique=True, nullable=False)
    provider_id: Mapped[str|None]=mapped_column(ForeignKey("ai_providers.id", ondelete="SET NULL"))
    model_name: Mapped[str|None]=mapped_column(String(200))
    question_solution: Mapped[QuestionSolution]=relationship(back_populates="ai_solution")

class PracticeSession(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="practice_sessions"
    knowledge_base_id: Mapped[str]=mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    learner_profile_id: Mapped[str|None]=mapped_column(ForeignKey("learner_profiles.id", ondelete="SET NULL"))
    mode: Mapped[str]=mapped_column(String(30), nullable=False)
    status: Mapped[str]=mapped_column(String(30), default="active", nullable=False, index=True)
    started_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    ended_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

class PracticeAttempt(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="practice_attempts"
    session_id: Mapped[str]=mapped_column(ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id: Mapped[str]=mapped_column(ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    answer_text: Mapped[str|None]=mapped_column(Text)
    is_correct: Mapped[bool|None]=mapped_column(Boolean)
    skipped: Mapped[bool]=mapped_column(Boolean, default=False, nullable=False)
    time_ms: Mapped[int|None]=mapped_column(Integer)
    confidence: Mapped[float|None]=mapped_column(Float)

class ReviewItem(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="review_items"
    knowledge_base_id: Mapped[str]=mapped_column(ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, index=True)
    entity_type: Mapped[str]=mapped_column(String(50), nullable=False)
    entity_id: Mapped[str]=mapped_column(String(36), nullable=False, index=True)
    reason: Mapped[str]=mapped_column(String(100), nullable=False)
    status: Mapped[str]=mapped_column(String(30), default="open", nullable=False, index=True)

class LearnerProfile(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="learner_profiles"
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

class TopicMastery(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="topic_mastery"
    learner_profile_id: Mapped[str]=mapped_column(ForeignKey("learner_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    topic_id: Mapped[str]=mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    mastery: Mapped[float]=mapped_column(Float, default=0.0, nullable=False)
    confidence: Mapped[float]=mapped_column(Float, default=0.0, nullable=False)
    __table_args__=(UniqueConstraint("learner_profile_id","topic_id"),)

class SkillState(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="skill_states"
    learner_profile_id: Mapped[str]=mapped_column(ForeignKey("learner_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    concept_id: Mapped[str]=mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    state: Mapped[str]=mapped_column(String(40), default="unknown", nullable=False)
    score: Mapped[float]=mapped_column(Float, default=0.0, nullable=False)
    __table_args__=(UniqueConstraint("learner_profile_id","concept_id"),)

class Prerequisite(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="prerequisites"
    prerequisite_concept_id: Mapped[str]=mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    dependent_concept_id: Mapped[str]=mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True)
    strength: Mapped[float|None]=mapped_column(Float)
    __table_args__=(UniqueConstraint("prerequisite_concept_id","dependent_concept_id"),)

class AnalyticsEvent(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="analytics_events"
    user_id: Mapped[str|None]=mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    knowledge_base_id: Mapped[str|None]=mapped_column(ForeignKey("knowledge_bases.id", ondelete="SET NULL"), index=True)
    event_type: Mapped[str]=mapped_column(String(100), nullable=False, index=True)
    occurred_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

class AIProvider(IdMixin, TimestampMixin, Base):
    __tablename__="ai_providers"
    user_id: Mapped[str]=mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_type: Mapped[str]=mapped_column(String(50), nullable=False)
    display_name: Mapped[str|None]=mapped_column(String(200))
    model_name: Mapped[str|None]=mapped_column(String(200))
    enabled: Mapped[bool]=mapped_column(Boolean, default=True, nullable=False)

class Credential(IdMixin, TimestampMixin, Base):
    __tablename__="credentials"
    ai_provider_id: Mapped[str]=mapped_column(ForeignKey("ai_providers.id", ondelete="CASCADE"), nullable=False, unique=True)
    secret_ciphertext: Mapped[str|None]=mapped_column(Text)
    secret_ref: Mapped[str|None]=mapped_column(String(500))
    key_fingerprint: Mapped[str|None]=mapped_column(String(128), index=True)

class ProcessingJob(IdMixin, TimestampMixin, JSONMixin, Base):
    __tablename__="processing_jobs"
    document_version_id: Mapped[str]=mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str]=mapped_column(String(30), default="queued", nullable=False, index=True)
    worker_task_id: Mapped[str|None]=mapped_column(String(200), index=True)
    attempts: Mapped[int]=mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

class ProcessingStage(IdMixin, TimestampMixin, Base):
    __tablename__="processing_stages"
    processing_job_id: Mapped[str]=mapped_column(ForeignKey("processing_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    stage_name: Mapped[str]=mapped_column(String(100), nullable=False)
    status: Mapped[str]=mapped_column(String(30), default="pending", nullable=False)
    ordinal: Mapped[int]=mapped_column(Integer, nullable=False)
    progress: Mapped[float]=mapped_column(Float, default=0.0, nullable=False)
    error_message: Mapped[str|None]=mapped_column(Text)
    started_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))

Index("ix_materials_sha256_media_type", Material.sha256, Material.media_type)
Index("ix_processing_stages_job_ordinal", ProcessingStage.processing_job_id, ProcessingStage.ordinal)
