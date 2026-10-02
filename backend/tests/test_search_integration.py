from sqlalchemy import text
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.models import (
    Block, Chapter, Concept, Document, DocumentVersion, Equation,
    KnowledgeBase, Material, Page, Provenance, Question, Section,
    Subtopic, Topic, User, Workspace,
)
from moduleiq.services.search_engine import search
from test_database import make_engine


def _create_search_tables(session: Session) -> None:
    session.execute(text(
        "CREATE TABLE search_entries ("
        "id VARCHAR(80) PRIMARY KEY, knowledge_base_id VARCHAR(36), kind VARCHAR(30), "
        "object_id VARCHAR(36), title VARCHAR(500), content TEXT, "
        "source_document_id VARCHAR(36), source_page_id VARCHAR(36))"
    ))
    session.execute(text(
        "CREATE TABLE search_index_state ("
        "knowledge_base_id VARCHAR(36) PRIMARY KEY, source_fingerprint VARCHAR(64), indexed_at DATETIME)"
    ))
    session.execute(text(
        "CREATE VIRTUAL TABLE search_entries_fts USING fts5("
        "entry_id UNINDEXED, knowledge_base_id UNINDEXED, kind UNINDEXED, "
        "object_id UNINDEXED, title, content, tokenize='unicode61')"
    ))


def test_search_finds_structured_objects_cross_document_and_preserves_source(tmp_path):
    engine = make_engine(tmp_path)
    from moduleiq.infrastructure.database.base import Base
    from moduleiq.infrastructure.database import models_import  # noqa: F401

    Base.metadata.create_all(engine)
    with Session(engine) as db:
        _create_search_tables(db)

        user = User(id="u1", email="search@example.com")
        workspace = Workspace(id="w1", owner=user, name="Search")
        kb = KnowledgeBase(id="kb1", workspace=workspace, name="Physics")
        m1 = Material(id="m1", knowledge_base=kb, name="Gauss Notes", media_type="application/pdf")
        m2 = Material(id="m2", knowledge_base=kb, name="Electrostatics Problems", media_type="application/pdf")
        d1 = Document(id="d1", material=m1, title="Gauss Law Notes")
        d2 = Document(id="d2", material=m2, title="Electrostatics Questions")
        v1 = DocumentVersion(id="v1", document=d1, version_number=1)
        v2 = DocumentVersion(id="v2", document=d2, version_number=1)
        p1 = Page(id="p1", document_version=v1, page_number=42)
        p2 = Page(id="p2", document_version=v2, page_number=7)
        b1 = Block(id="b1", page=p1, block_type="paragraph", ordinal=1, text="Gauss law uses cylindrical symmetry for an infinite line charge.")
        section1 = Section(id="s1", document_version_id=v1.id, title="Electrostatics")
        chapter1 = Chapter(id="c1", section=section1, title="Electric Flux", ordinal=1)
        topic1 = Topic(id="t1", chapter=chapter1, name="Gauss Law")
        sub1 = Subtopic(id="st1", topic=topic1, name="Symmetry")
        concept1 = Concept(id="co1", subtopic=sub1, name="Cylindrical symmetry", definition="Use cylindrical Gaussian surfaces for line-charge problems.")
        prov1 = Provenance(id="prov1", source_document_id=d2.id, source_page_id=p2.id, source_kind="question")
        q1 = Question(
            id="q1",
            knowledge_base_id=kb.id,
            text="Which Gaussian surface matches cylindrical symmetry?",
            question_type="multiple_choice",
            provenance_id="prov1",
        )
        e1 = Equation(id="e1", page_id=p1.id, latex="Phi_E = q/epsilon_0", source_text="Gauss law equation")

        db.add_all([user, workspace, kb, m1, m2, d1, d2, v1, v2, p1, p2, b1, section1, chapter1, topic1, sub1, concept1])
        db.commit()
        db.add_all([prov1, q1])
        db.commit()
        db.add(e1)
        db.commit()

        exact = search(db, "kb1", "Gauss law")
        assert exact["results"]
        assert any(r["kind"] in {"document", "topic", "question", "block"} for r in exact["results"])

        topic = search(db, "kb1", "cylindrical symmetry", kind="concept")
        assert topic["results"]
        assert topic["results"][0]["id"] == "co1"

        filtered = search(db, "kb1", "symmetry", document_id="d2")
        assert all(r["source"]["document_id"] == "d2" for r in filtered["results"])

        semantic = search(db, "kb1", "cylindrical")
        assert any(c["name"] == "Cylindrical symmetry" for c in semantic["related_concepts"])
