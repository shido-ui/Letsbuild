from pypdf import PdfWriter
import pytest

from moduleiq.services import ingestion


def test_pdf_page_limit_is_enforced(tmp_path, monkeypatch):
    path = tmp_path / "large.pdf"
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    with path.open("wb") as fh:
        writer.write(fh)

    monkeypatch.setattr(ingestion.settings, "max_pdf_pages", 0)

    with pytest.raises(ingestion.IngestionError, match="page limit"):
        ingestion._pdf_metadata(path)
