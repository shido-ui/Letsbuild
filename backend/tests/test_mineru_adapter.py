from __future__ import annotations

import sys
import types
from pathlib import Path

from moduleiq.infrastructure.document_engine.mineru_adapter import (
    MinerUUnavailable,
    extract_with_mineru,
)

def test_mineru_missing_is_explicit(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "mineru", None)
    try:
        extract_with_mineru(tmp_path / "x.pdf", tmp_path / "out")
    except MinerUUnavailable as exc:
        assert "MinerU is not installed" in str(exc)
    else:
        raise AssertionError("Missing MinerU must be explicit")

def test_adapter_preserves_native_outputs(tmp_path, monkeypatch):
    class FakeResult:
        pages = [object(), object()]
        def to_json(self): return '{"schema_version":"test"}'
        def markdown(self): return "# extracted"
        def structured_content(self): return {"pages": 2}
        def save(self, writer):
            writer.write_string("assets/figure.txt", "asset")

    fake_parser = types.ModuleType("mineru.parser")
    fake_parser.parse = lambda *args, **kwargs: FakeResult()
    fake_writer = types.ModuleType("mineru.parser.writer")
    class FakeWriter:
        def __init__(self, root): self.root=Path(root)
        def write_string(self, name, value):
            path=self.root/name; path.parent.mkdir(parents=True,exist_ok=True); path.write_text(value)
    fake_writer.FileBasedDataWriter = FakeWriter
    fake_pkg = types.ModuleType("mineru")
    fake_pkg.__version__ = "4.0.10"
    monkeypatch.setitem(sys.modules, "mineru", fake_pkg)
    monkeypatch.setitem(sys.modules, "mineru.parser", fake_parser)
    monkeypatch.setitem(sys.modules, "mineru.parser.writer", fake_writer)

    result=extract_with_mineru(tmp_path/"source.pdf",tmp_path/"out")
    assert result.engine=="mineru"
    assert result.engine_version=="4.0.10"
    assert result.page_count==2
    assert result.middle_json_path.read_text()=="{\"schema_version\":\"test\"}"
    assert (tmp_path/"out"/"assets"/"figure.txt").exists()
