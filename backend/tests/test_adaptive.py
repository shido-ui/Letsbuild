from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database import models_import  # noqa: F401
from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database.models import (
    Classification, KnowledgeBase, LearnerProfile, Question, Topic, User, Workspace,
    PracticeSession, PracticeAttempt,
)
from moduleiq.services.adaptive import update_from_attempt, mastery, recommendations


def make_engine(tmp_path: Path):
    e = create_engine(f"sqlite:///{tmp_path / 'adaptive.db'}")
    @event.listens_for(e, "connect")
    def fk(conn, _):
        conn.execute("PRAGMA foreign_keys=ON")
    return e


def test_adaptive_mastery_updates_and_recommends(tmp_path):
    e = make_engine(tmp_path)
    Base.metadata.create_all(e)
    with Session(e) as db:
        user = User(id="u1", email="adaptive@example.com")
        workspace = Workspace(id="w1", owner=user, name="Workspace")
        kb = KnowledgeBase(id="kb1", workspace=workspace, name="Physics")
        profile = LearnerProfile(id="lp1", user_id="u1")
        topic = Topic(id="t1", name="Kinematics")
        classification = Classification(id="cl1", topic="Kinematics")
        q = Question(id="q1", knowledge_base_id="kb1", text="Velocity?", question_type="multiple_choice", classification_id="cl1")
        session = PracticeSession(id="ps1", knowledge_base_id="kb1", learner_profile_id="lp1", mode="fast")
        attempt = PracticeAttempt(id="a1", session_id="ps1", question_id="q1", is_correct=False, skipped=False)
        db.add_all([user, workspace, kb, profile, topic, classification, q, session, attempt])
        db.commit()

        updated = update_from_attempt(db, attempt)
        db.commit()
        assert updated and updated["mastery"] < 0.0 + 0.01
        rows = mastery(db, "lp1", "kb1")
        assert rows[0]["needs_review"] is True
        recs = recommendations(db, "lp1", "kb1")
        assert recs and recs[0]["question_id"] == "q1"
