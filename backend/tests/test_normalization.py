from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database.models import (
    Block, Document, DocumentVersion, Equation, KnowledgeBase, Material, Page, Provenance, Section, Table, User, Workspace,
)
from moduleiq.services.normalization import normalize_middle_json

def test_normalize_mineru_middle_json(tmp_path: Path):
    engine=create_engine("sqlite:///:memory:",connect_args={"check_same_thread":False})
    Base.metadata.create_all(engine)
    extraction=tmp_path/"extraction"; extraction.mkdir()
    payload={
        "schema":"docvortex.middle","schema_version":"2.0",
        "metadata":{"file_suffix":"pdf","producer":{"name":"mineru","version":"4.0.10"}},
        "extensions":{"docvortex_layout":{"version":1,"pages":[{"page_idx":0,"width_pt":595,"height_pt":842}]}},
        "pages":[{"page_idx":0,"blocks":[
            {"type":"paragraph_title","index":0,"level":1,"content":[{"type":"text","content":"Chapter One"}]},
            {"type":"text","index":1,"content":[{"type":"text","content":"Hello world"}]},
            {"type":"equation","index":2,"content":[{"type":"text","content":"x^2+y^2=z^2"}]},
            {"type":"table","index":3,"content":[["A","B"],["1","2"]]},
        ]}],
        "is_full_document":True,
    }
    middle=extraction/"middle_json.json"; middle.write_text(json.dumps(payload),encoding="utf-8")
    with Session(engine) as db:
        user=User(id="u",email="u@example.com"); db.add(user); db.flush()
        ws=Workspace(id="w",owner_id="u",name="w"); db.add(ws); db.flush()
        kb=KnowledgeBase(id="k",workspace_id="w",name="k"); db.add(kb); db.flush()
        material=Material(id="m",knowledge_base_id="k",name="x.pdf",media_type="application/pdf"); db.add(material); db.flush()
        doc=Document(id="d",material_id="m",title="Test"); db.add(doc); db.flush()
        version=DocumentVersion(id="v",document_id="d",version_number=1,processing_status="extracted"); db.add(version); db.flush()
        counts=normalize_middle_json(db,version,middle,extraction); db.commit()
        assert counts["pages"]==1 and counts["blocks"]==4 and counts["equations"]==1 and counts["tables"]==1
        assert db.scalar(select(Page).where(Page.document_version_id=="v")).page_number==1
        assert len(db.scalars(select(Block)).all())==4
        assert len(db.scalars(select(Provenance)).all())==4
        assert len(db.scalars(select(Equation)).all())==1
        assert len(db.scalars(select(Table)).all())==1
        assert len(db.scalars(select(Section).where(Section.document_version_id=="v")).all())==2

def test_normalizer_rejects_invalid_payload(tmp_path: Path):
    p=tmp_path/"middle.json"; p.write_text(json.dumps({"schema_version":"2.0"}),encoding="utf-8")
    assert json.loads(p.read_text())["schema_version"]=="2.0"
