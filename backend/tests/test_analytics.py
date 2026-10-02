from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import select, create_engine, event
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database import models_import  # noqa: F401

from moduleiq.infrastructure.database.models import (
    AnalyticsEvent,
    Classification,
    DifficultyAssessment,
    KnowledgeBase,
    LearnerProfile,
    PracticeAttempt,
    PracticeSession,
    Topic,
    TopicMastery,
    User,
    Workspace,
    Chapter,
    Section,
)
from moduleiq.services.analytics import get_summary, log_event


def make_db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'analytics.db'}")
    @event.listens_for(engine, "connect")
    def enable_fk(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    return Session(engine)


def roots(db):
    user = User(id=str(uuid4()), email="analytics@example.com")
    db.add(user)
    db.flush()
    ws = Workspace(id=str(uuid4()), owner_id=user.id, name="Analytics")
    db.add(ws)
    db.flush()
    kb = KnowledgeBase(id=str(uuid4()), workspace_id=ws.id, name="Physics")
    db.add(kb)
    db.flush()
    section = Section(id=str(uuid4()), title="Mechanics")
    db.add(section)
    db.flush()
    chapter = Chapter(id=str(uuid4()), section_id=section.id, title="Kinematics", ordinal=1)
    db.add(chapter)
    db.flush()
    topic = Topic(id=str(uuid4()), chapter_id=chapter.id, name="Motion")
    db.add(topic)
    db.flush()
    profile = LearnerProfile(id=str(uuid4()), user_id=user.id)
    db.add(profile)
    db.flush()
    mastery = TopicMastery(id=str(uuid4()), learner_profile_id=profile.id, topic_id=topic.id, mastery=0.62, confidence=0.71)
    db.add(mastery)
    db.flush()
    questions = [Question(id=str(uuid4()), knowledge_base_id=kb.id, text=f"Question {i}", question_type="mcq") for i in range(3)]
    db.add_all(questions)
    db.flush()
    return user, kb, topic, profile, questions


def test_analytics_summary_uses_persisted_practice_and_mastery(tmp_path):
    db = make_db(tmp_path)
    user, kb, topic, profile, questions = roots(db)
    session = PracticeSession(
        id=str(uuid4()), knowledge_base_id=kb.id, learner_profile_id=profile.id,
        mode="fast", status="completed",
        started_at=datetime.now().astimezone() - timedelta(minutes=10),
        ended_at=datetime.now().astimezone(),
        metadata_json={"question_ids": []},
    )
    db.add(session)
    db.flush()
    db.add_all([
        PracticeAttempt(id=str(uuid4()), session_id=session.id, question_id=questions[0].id, is_correct=True, skipped=False, time_ms=1200),
        PracticeAttempt(id=str(uuid4()), session_id=session.id, question_id=questions[1].id, is_correct=False, skipped=False, time_ms=1800),
        PracticeAttempt(id=str(uuid4()), session_id=session.id, question_id=questions[2].id, is_correct=None, skipped=True),
    ])
    db.flush()
    log_event(db, "practice_session_completed", user_id=user.id, knowledge_base_id=kb.id, metadata={"score": 50})
    db.commit()

    summary = get_summary(db, kb.id)
    assert summary["sessions"] == 1
    assert summary["questions_answered"] == 2
    assert summary["questions_correct"] == 1
    assert summary["accuracy"] == 50.0
    assert summary["avg_time_ms"] == 1500
    assert summary["active_topics"] == 1
    assert summary["overall_mastery"] == 62.0
    assert summary["weak_topics"][0]["topic"] == "Motion"
    assert summary["recent_events"][0]["event_type"] == "practice_session_completed"
    db.close()
