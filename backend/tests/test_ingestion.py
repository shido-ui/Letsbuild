from __future__ import annotations
from pathlib import Path

import pytest
from pypdf import PdfWriter
from starlette.datastructures import UploadFile

from moduleiq.infrastructure.database.base import Base
from moduleiq.infrastructure.database import models_import  # noqa: F401
from moduleiq.infrastructure.database.models import ProcessingJob
from moduleiq.services import ingestion
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

def make_db(tmp_path: Path):
    engine=create_engine(f"sqlite:///{tmp_path/'test.db'}")
    @event.listens_for(engine,"connect")
    def fk(dbapi_connection,_): dbapi_connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(engine)
    return engine

def make_pdf(path: Path):
    writer=PdfWriter()
    writer.add_blank_page(width=612,height=792)
    with path.open("wb") as fh: writer.write(fh)

def test_real_pdf_creates_material_document_and_job(tmp_path,monkeypatch):
    pdf=tmp_path/"notes.pdf"; make_pdf(pdf)
    storage=tmp_path/"storage"; monkeypatch.setattr(ingestion.settings,"storage_root",str(storage))
    engine=make_db(tmp_path)
    with Session(engine) as db, pdf.open("rb") as fh:
        upload=UploadFile(file=fh,filename="notes.pdf",headers=None)
        result=ingestion.create_ingestion_job(db,upload)
        assert result["page_count"]==1
        assert result["status"]=="queued"
        assert result["sha256"]
        assert Path(result["knowledge_base_id"]).name == result["knowledge_base_id"]
        assert db.get(ProcessingJob,result["processing_job_id"]) is not None
        assert list(storage.rglob("*.pdf"))

def test_duplicate_rejected(tmp_path,monkeypatch):
    pdf=tmp_path/"notes.pdf"; make_pdf(pdf)
    storage=tmp_path/"storage"; monkeypatch.setattr(ingestion.settings,"storage_root",str(storage))
    engine=make_db(tmp_path)
    with Session(engine) as db, pdf.open("rb") as fh:
        ingestion.create_ingestion_job(db,UploadFile(file=fh,filename="notes.pdf"))
    with Session(engine) as db, pdf.open("rb") as fh:
        with pytest.raises(ingestion.IngestionError,match="already exists"):
            ingestion.create_ingestion_job(db,UploadFile(file=fh,filename="notes-copy.pdf"))
