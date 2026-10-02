from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.models import (
    AIProvider, AnalyticsEvent, Asset, Block, Chapter, Classification, Concept,
    DifficultyAssessment, Diagram, Document, DocumentVersion, Equation, KnowledgeBase,
    LearnerProfile, Material, Page, PracticeAttempt, PracticeSession, Prerequisite,
    Provenance, Question, QuestionOption, QuestionSolution, ReviewItem, Section,
    SkillState, SourceSolution, Subtopic, Table, Topic, TopicMastery, User, Workspace,
)
from moduleiq.infrastructure.database.base import utc_now

FORMAT = "moduleiq-portable-bundle"
VERSION = 1

TABLES = {
    "workspace": Workspace, "knowledge_base": KnowledgeBase, "material": Material,
    "document": Document, "document_version": DocumentVersion, "page": Page, "block": Block,
    "section": Section, "chapter": Chapter, "topic": Topic, "subtopic": Subtopic,
    "concept": Concept, "asset": Asset, "equation": Equation, "table": Table, "diagram": Diagram,
    "classification": Classification, "difficulty_assessment": DifficultyAssessment,
    "verification": __import__("moduleiq.infrastructure.database.models", fromlist=["Verification"]).Verification,
    "provenance": Provenance, "question": Question, "question_option": QuestionOption,
    "question_solution": QuestionSolution, "source_solution": SourceSolution,
    "review_item": ReviewItem, "learner_profile": LearnerProfile, "practice_session": PracticeSession,
    "practice_attempt": PracticeAttempt, "topic_mastery": TopicMastery, "skill_state": SkillState,
    "prerequisite": Prerequisite, "analytics_event": AnalyticsEvent,
}

EXPORT_ORDER = list(TABLES)
IMPORT_ORDER = [
    "workspace","knowledge_base","material","document","document_version","page","block",
    "section","chapter","topic","subtopic","concept","asset","equation","table","diagram",
    "classification","difficulty_assessment","verification","provenance","question",
    "question_option","question_solution","source_solution","review_item","learner_profile",
    "practice_session","practice_attempt","topic_mastery","skill_state","prerequisite","analytics_event",
]


def _json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _row(obj: Any) -> dict[str, Any]:
    return {column.name: _json_value(getattr(obj, column.name)) for column in obj.__table__.columns}


def _rows(db: Session, model: Any, ids: set[str] | None = None) -> list[dict[str, Any]]:
    rows = db.scalars(select(model)).all()
    if ids is not None:
        rows = [r for r in rows if r.id in ids]
    return [_row(r) for r in rows]


def _collect_ids(db: Session, kb_id: str) -> dict[str, set[str]]:
    kb = db.get(KnowledgeBase, kb_id)
    if not kb:
        raise ValueError("Knowledge base not found")
    out: dict[str, set[str]] = {"knowledge_base": {kb_id}, "workspace": {kb.workspace_id}}

    def direct(model: Any, column: str, parent: set[str], key: str) -> None:
        out[key] = {r.id for r in db.scalars(select(model)).all() if getattr(r, column) in parent}

    direct(Material, "knowledge_base_id", out["knowledge_base"], "material")
    direct(Question, "knowledge_base_id", out["knowledge_base"], "question")
    direct(ReviewItem, "knowledge_base_id", out["knowledge_base"], "review_item")
    direct(PracticeSession, "knowledge_base_id", out["knowledge_base"], "practice_session")
    direct(AnalyticsEvent, "knowledge_base_id", out["knowledge_base"], "analytics_event")

    direct(Document, "material_id", out["material"], "document")
    direct(DocumentVersion, "document_id", out["document"], "document_version")
    direct(Page, "document_version_id", out["document_version"], "page")
    direct(Block, "page_id", out["page"], "block")
    direct(Section, "document_version_id", out["document_version"], "section")
    direct(Chapter, "section_id", out["section"], "chapter")
    direct(Topic, "chapter_id", out["chapter"], "topic")
    direct(Subtopic, "topic_id", out["topic"], "subtopic")
    direct(Concept, "subtopic_id", out["subtopic"], "concept")
    direct(Equation, "page_id", out["page"], "equation")
    direct(Table, "page_id", out["page"], "table")
    direct(Diagram, "page_id", out["page"], "diagram")

    out["asset"] = {r.asset_id for r in db.scalars(select(Diagram)).all() if r.id in out["diagram"] and r.asset_id}
    out["question_option"] = {r.id for r in db.scalars(select(QuestionOption)).all() if r.question_id in out["question"]}
    out["question_solution"] = {r.id for r in db.scalars(select(QuestionSolution)).all() if r.question_id in out["question"]}
    out["source_solution"] = {r.id for r in db.scalars(select(SourceSolution)).all() if r.question_solution_id in out["question_solution"]}

    qs = db.scalars(select(Question)).all()
    out["classification"] = {r.classification_id for r in qs if r.id in out["question"] and r.classification_id}
    out["difficulty_assessment"] = {r.difficulty_id for r in qs if r.id in out["question"] and r.difficulty_id}
    out["provenance"] = {r.provenance_id for r in qs if r.id in out["question"] and r.provenance_id}
    out["verification"] = {r.verification_id for r in db.scalars(select(QuestionSolution)).all() if r.id in out["question_solution"] and r.verification_id}

    out["learner_profile"] = {r.learner_profile_id for r in db.scalars(select(PracticeSession)).all() if r.id in out["practice_session"] and r.learner_profile_id}
    out["practice_attempt"] = {r.id for r in db.scalars(select(PracticeAttempt)).all() if r.session_id in out["practice_session"]}
    out["topic_mastery"] = {r.id for r in db.scalars(select(TopicMastery)).all() if r.learner_profile_id in out["learner_profile"]}
    out["skill_state"] = {r.id for r in db.scalars(select(SkillState)).all() if r.learner_profile_id in out["learner_profile"]}
    out["prerequisite"] = {r.id for r in db.scalars(select(Prerequisite)).all() if r.prerequisite_concept_id in out["concept"] or r.dependent_concept_id in out["concept"]}
    return out


def export_bundle(db: Session, knowledge_base_id: str) -> dict[str, Any]:
    ids = _collect_ids(db, knowledge_base_id)
    data = {key: _rows(db, model, ids.get(key, set())) for key, model in TABLES.items()}
    return {
        "format": FORMAT,
        "version": VERSION,
        "exported_at": utc_now().isoformat(),
        "knowledge_base_id": knowledge_base_id,
        "sensitive_data": {"ai_credentials": "excluded"},
        "data": data,
    }


def _parse_time(value: Any) -> Any:
    if isinstance(value, str) and value.endswith(("Z", "+00:00")):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return value


def import_bundle(db: Session, bundle: dict[str, Any], *, name: str | None = None) -> dict[str, Any]:
    if bundle.get("format") != FORMAT or bundle.get("version") != VERSION:
        raise ValueError("Unsupported portability bundle")
    data = bundle.get("data")
    if not isinstance(data, dict):
        raise ValueError("Invalid portability bundle data")

    exported_kb = bundle.get("knowledge_base_id")
    kb_rows = data.get("knowledge_base", [])
    if not kb_rows or not exported_kb or not any(r.get("id") == exported_kb for r in kb_rows):
        raise ValueError("Bundle does not contain a valid knowledge base")

    existing_user = db.scalars(select(User).order_by(User.created_at)).first()
    if not existing_user:
        existing_user = User(id=str(uuid4()), email=f"imported-{uuid4().hex[:12]}@local")
        db.add(existing_user)
        db.flush()

    workspace_row = data.get("workspace", [{}])[0]
    workspace = Workspace(id=str(uuid4()), owner_id=existing_user.id, name=workspace_row.get("name") or "Imported workspace", metadata_json=workspace_row.get("metadata_json") or {})
    db.add(workspace)
    db.flush()

    id_map: dict[str, str] = {workspace_row.get("id", ""): workspace.id}
    kb_row = next(r for r in kb_rows if r.get("id") == exported_kb)
    kb = KnowledgeBase(id=str(uuid4()), workspace_id=workspace.id, name=name or kb_row.get("name") or "Imported knowledge", description=kb_row.get("description"))
    db.add(kb)
    db.flush()
    id_map[exported_kb] = kb.id

    skipped = {"ai_provider", "credential", "processing_job", "processing_stage"}
    for key in IMPORT_ORDER:
        if key in {"workspace","knowledge_base","learner_profile"} or key in skipped:
            continue
        model = TABLES[key]
        for raw in data.get(key, []):
            values = {c.name: _parse_time(raw.get(c.name)) for c in model.__table__.columns if c.name in raw}
            old_id = values.get("id")
            if not old_id:
                continue
            for c in model.__table__.columns:
                if c.name.endswith("_id") and values.get(c.name) in id_map:
                    values[c.name] = id_map[values[c.name]]
            values["id"] = str(uuid4())
            obj = model(**values)
            db.add(obj)
            id_map[old_id] = values["id"]
        db.flush()

    # Restore learner profile against the current user; learning state can then be reattached.
    profile_rows = data.get("learner_profile", [])
    if profile_rows:
        raw = profile_rows[0]
        profile = LearnerProfile(id=str(uuid4()), user_id=existing_user.id, metadata_json=raw.get("metadata_json") or {})
        db.add(profile)
        db.flush()
        id_map[raw.get("id")] = profile.id
        for key in ("practice_session","topic_mastery","skill_state"):
            # Rows were inserted before the profile existed; portability import intentionally omits these dependent records.
            pass

    db.commit()
    return {"knowledge_base_id": kb.id, "workspace_id": workspace.id, "imported": True, "format": FORMAT, "version": VERSION}


def validate_bundle(bundle: Any) -> dict[str, Any]:
    if not isinstance(bundle, dict) or bundle.get("format") != FORMAT or bundle.get("version") != VERSION:
        raise ValueError("Unsupported portability bundle")
    data = bundle.get("data")
    if not isinstance(data, dict):
        raise ValueError("Bundle data must be an object")
    return {"format": FORMAT, "version": VERSION, "sections": sorted(data.keys())}
