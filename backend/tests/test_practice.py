from pathlib import Path

from sqlalchemy import event
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database import models_import  # noqa: F401
from moduleiq.infrastructure.database.models import (
    Chapter, Document, DocumentVersion, KnowledgeBase, Material, Page,
    Question, QuestionOption, Section, Topic, User, Workspace,
)
from moduleiq.services.practice import (
    attempt, create_session, finish_session, get_results, pause_session, resume_session,
)


def engine(tmp_path: Path):
    e = create_engine(f"sqlite:///{tmp_path / 'practice.db'}")
    @event.listens_for(e, "connect")
    def fk(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
    return e


def seed(db: Session):
    user = User(id="u1", email="practice@example.com")
    workspace = Workspace(id="w1", owner=user, name="Workspace")
    kb = KnowledgeBase(id="kb1", workspace=workspace, name="Physics")
    material = Material(id="m1", knowledge_base=kb, name="Notes", media_type="application/pdf")
    document = Document(id="d1", material=material, title="Notes")
    version = DocumentVersion(id="v1", document=document, version_number=1)
    page = Page(id="p1", document_version_id="v1", page_number=1)
    section = Section(id="s1", document_version_id="v1", title="Mechanics")
    chapter = Chapter(id="c1", section_id="s1", title="Kinematics", ordinal=1)
    topic = Topic(id="t1", chapter_id="c1", name="Motion")
    q1 = Question(id="q1", knowledge_base_id="kb1", text="2+2?", question_type="multiple_choice")
    q2 = Question(id="q2", knowledge_base_id="kb1", text="3+3?", question_type="multiple_choice")
    o11 = QuestionOption(id="o11", question_id="q1", ordinal=1, option_text="4", is_correct=True)
    o12 = QuestionOption(id="o12", question_id="q1", ordinal=2, option_text="5", is_correct=False)
    o21 = QuestionOption(id="o21", question_id="q2", ordinal=1, option_text="6", is_correct=True)
    o22 = QuestionOption(id="o22", question_id="q2", ordinal=2, option_text="7", is_correct=False)
    db.add_all([user, workspace, kb])
    db.commit()
    db.add_all([material, document, version, page, section, chapter, topic])
    db.commit()
    db.add_all([q1, q2])
    db.commit()
    db.add_all([o11, o12, o21, o22])
    db.commit()


def test_practice_session_persists_pause_resume_answer_and_results(tmp_path):
    e = engine(tmp_path)
    Base.metadata.create_all(e)
    with Session(e) as db:
        seed(db)
        session = create_session(db, "kb1", mode="fast", limit=2)
        sid = session["id"]
        assert session["status"] == "active"
        assert session["total_questions"] == 2

        first = session["current_question"]["id"]
        paused = pause_session(db, sid)
        assert paused["status"] == "paused"
        resumed = resume_session(db, sid)
        assert resumed["status"] == "active"

        after = attempt(db, sid, question_id=first, answer_text="4")
        assert after["attempts"][0]["is_correct"] is True
        assert after["current_index"] == 1

        second = after["current_question"]["id"]
        completed = attempt(db, sid, question_id=second, skipped=True)
        assert completed["status"] == "completed"
        result = get_results(db, sid)
        assert result["correct"] == 1
        assert result["skipped"] == 1
        assert result["score"] == 50.0

        # A fresh SQLAlchemy session sees the same state: refresh/restart cannot lose the session.
        with Session(e) as fresh:
            restored = get_results(fresh, sid)
            assert restored["total_questions"] == 2
            assert restored["attempted"] == 2
