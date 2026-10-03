from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database import models_import  # noqa: F401
from moduleiq.infrastructure.database.models import User, Workspace, KnowledgeBase, Question, QuestionOption
from moduleiq.infrastructure.database.session import get_db
from moduleiq.main import app
from moduleiq.core.dependencies import get_current_user


def test_api_learning_journey(tmp_path):
    engine=create_engine(f"sqlite:///{tmp_path / 'e2e.db'}")
    @event.listens_for(engine,"connect")
    def fk(dbapi_connection,_): dbapi_connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        user=User(id=str(uuid4()),email="local@moduleiq",display_name="Local")
        db.add(user); db.flush()
        ws=Workspace(id=str(uuid4()),owner_id=user.id,name="Personal"); db.add(ws); db.flush()
        kb=KnowledgeBase(id=str(uuid4()),workspace_id=ws.id,name="Physics"); db.add(kb); db.flush()
        q=Question(id=str(uuid4()),knowledge_base_id=kb.id,text="2 + 2 = ?",question_type="multiple_choice")
        db.add(q); db.flush()
        db.add_all([
            QuestionOption(id=str(uuid4()),question_id=q.id,ordinal=1,option_text="4",is_correct=True),
            QuestionOption(id=str(uuid4()),question_id=q.id,ordinal=2,option_text="5",is_correct=False),
        ])
        db.commit()
        kb_id, q_id = kb.id, q.id

    def override_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db]=override_db
    app.dependency_overrides[get_current_user]=lambda: user
    try:
        client=TestClient(app)
        listed=client.get("/api/ingestion/knowledge-bases")
        assert listed.status_code==200 and listed.json()[0]["id"]==kb_id

        session=client.post("/api/practice/sessions",json={"knowledge_base_id":kb_id,"mode":"fast","limit":1})
        assert session.status_code==200
        sid=session.json()["id"]
        question=session.json()["current_question"]
        answer=question["options"][0]["id"]

        attempt=client.post(f"/api/practice/sessions/{sid}/attempt",json={"question_id":q_id,"answer_text":answer})
        assert attempt.status_code==200 and attempt.json()["status"]=="completed"

        results=client.get(f"/api/practice/sessions/{sid}/results")
        assert results.status_code==200 and results.json()["correct"]==1

        review=client.post("/api/review/items",json={"knowledge_base_id":kb_id,"entity_type":"question","entity_id":q_id,"reason":"E2E review"})
        assert review.status_code==200
        review_id=review.json()["id"]
        assert client.patch(f"/api/review/items/{review_id}",json={"status":"resolved"}).status_code==200

        analytics=client.get(f"/api/analytics/summary?knowledge_base_id={kb_id}&days=30")
        assert analytics.status_code==200 and analytics.json()["questions_answered"]==1

        exported=client.get(f"/api/portability/export?knowledge_base_id={kb_id}")
        assert exported.status_code==200
        bundle=exported.json()
        assert client.post("/api/portability/validate",json=bundle).status_code==200
    finally:
        app.dependency_overrides.clear()
