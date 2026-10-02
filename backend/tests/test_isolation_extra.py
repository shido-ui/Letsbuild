from uuid import uuid4

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session

from moduleiq.core.security import require_local_profile
from moduleiq.infrastructure.database import models_import  # noqa: F401
from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database.models import LearnerProfile, User


def make_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'isolation-extra.db'}")

    @event.listens_for(engine, "connect")
    def fk(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    return engine


def test_foreign_learner_profile_isolation(tmp_path):
    engine = make_engine(tmp_path)
    with Session(engine) as db:
        local = User(id=str(uuid4()), email="local@moduleiq")
        other = User(id=str(uuid4()), email="foreign@example.com")
        db.add_all([local, other])
        db.flush()
        foreign_profile = LearnerProfile(id=str(uuid4()), user_id=other.id)
        db.add(foreign_profile)
        db.commit()

        try:
            require_local_profile(db, foreign_profile.id)
        except ValueError as exc:
            assert "not found" in str(exc).lower()
        else:
            raise AssertionError("foreign learner profile was accessible")
