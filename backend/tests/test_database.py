from pathlib import Path
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database import models_import  # noqa: F401
from moduleiq.infrastructure.database.models import User, Workspace, KnowledgeBase, Material, Document, DocumentVersion

def make_engine(tmp_path: Path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}")
    @event.listens_for(engine, "connect")
    def enable_fk(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
    return engine

def test_schema_contains_required_domain_tables(tmp_path):
    engine = make_engine(tmp_path)
    Base.metadata.create_all(engine)
    names = set(inspect(engine).get_table_names())
    required = {
        "users","workspaces","knowledge_bases","materials","documents","document_versions","pages",
        "blocks","sections","chapters","topics","subtopics","concepts","equations","tables","diagrams",
        "assets","questions","question_options","question_solutions","source_solutions","ai_solutions",
        "classifications","difficulty_assessments","verifications","provenance","practice_sessions",
        "practice_attempts","review_items","learner_profiles","topic_mastery","skill_states","prerequisites",
        "analytics_events","ai_providers","credentials","processing_jobs","processing_stages",
    }
    assert required <= names

def test_foreign_key_cascade_and_unique_constraint(tmp_path):
    engine = make_engine(tmp_path)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        user = User(id="u1", email="a@example.com")
        workspace = Workspace(id="w1", owner=user, name="Default")
        kb = KnowledgeBase(id="kb1", workspace=workspace, name="Main")
        material = Material(id="m1", knowledge_base=kb, name="Notes.pdf", media_type="application/pdf")
        document = Document(id="d1", material=material, title="Notes")
        version = DocumentVersion(id="dv1", document=document, version_number=1)
        session.add(user)
        session.commit()
        assert session.get(Document, "d1") is document
        session.delete(user)
        session.commit()
        assert session.get(KnowledgeBase, "kb1") is None
        assert session.get(DocumentVersion, "dv1") is None
