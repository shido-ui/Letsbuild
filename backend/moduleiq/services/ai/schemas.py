from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Literal

class SourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_kind: str
    source_id: str | None = None
    page_id: str | None = None
    block_id: str | None = None
    locator: str | None = None

class ClassificationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: str | None = None
    topic: str | None = None
    subtopic: str | None = None
    confidence: float = Field(ge=0, le=1)
    source_references: list[SourceReference] = []

class ExtractionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: str
    text: str
    source_references: list[SourceReference] = []

class ExtractionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    items: list[ExtractionItem]
    source_references: list[SourceReference] = []

class SolutionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str
    steps: list[str] = []
    confidence: float = Field(ge=0, le=1)
    source_references: list[SourceReference] = []

class VerificationOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["verified", "uncertain", "failed"]
    confidence: float = Field(ge=0, le=1)
    notes: str
    source_references: list[SourceReference] = []

class SummaryOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str
    key_points: list[str] = []
    source_references: list[SourceReference] = []

class GeneratedQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    question_type: str
    options: list[str] = []
    answer: str | None = None
    source_references: list[SourceReference] = []

class QuestionsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    questions: list[GeneratedQuestion]
    source_references: list[SourceReference] = []

class AIExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    operation: str
    provider: str
    model: str
    attempts: int
    cached: bool = False
    output: Any
    source_references: list[SourceReference] = []


class KnowledgeConceptGroup(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    concepts: list[str] = []

class KnowledgeTopic(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str
    subtopics: list[KnowledgeConceptGroup] = []

class KnowledgePrerequisite(BaseModel):
    model_config = ConfigDict(extra='forbid')
    prerequisite: str
    dependent: str
    strength: float = Field(default=0.5, ge=0, le=1)

class KnowledgeOutput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    subject: str | None = None
    section: str | None = None
    chapter: str | None = None
    confidence: float = Field(ge=0, le=1)
    topics: list[KnowledgeTopic] = []
    prerequisites: list[KnowledgePrerequisite] = []
    related_concepts: list[tuple[str, str]] = []
    source_references: list[dict] = []
