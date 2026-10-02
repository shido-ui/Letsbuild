from uuid import uuid4

from moduleiq.infrastructure.database.models import KnowledgeBase, User, Workspace
from moduleiq.services.portability import export_bundle, import_bundle, validate_bundle


def test_portability_round_trip(tmp_path):
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import Session
    from moduleiq.infrastructure.database.base import Base
    from moduleiq.infrastructure.database import models_import  # noqa: F401

    engine = create_engine(f"sqlite:///{tmp_path / 'portable.db'}")
    @event.listens_for(engine, "connect")
    def enable_fk(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        user = User(id=str(uuid4()), email="portable@example.com")
        db.add(user)
        db.flush()
        ws = Workspace(id=str(uuid4()), owner_id=user.id, name="Portable")
        db.add(ws)
        db.flush()
        kb = KnowledgeBase(id=str(uuid4()), workspace_id=ws.id, name="Physics", description="Portable test")
        db.add(kb)
        db.commit()

        bundle = export_bundle(db, kb.id)
        assert bundle["format"] == "moduleiq-portable-bundle"
        assert bundle["version"] == 1
        assert bundle["sensitive_data"]["ai_credentials"] == "excluded"
        assert validate_bundle(bundle)["format"] == bundle["format"]

        imported = import_bundle(db, bundle, name="Imported Physics")
        assert imported["imported"] is True
        assert imported["knowledge_base_id"] != kb.id
        assert db.get(KnowledgeBase, imported["knowledge_base_id"]).name == "Imported Physics"


def test_invalid_portability_bundle_rejected():
    try:
        validate_bundle({"format": "wrong", "version": 1, "data": {}})
    except ValueError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("invalid bundle was accepted")
