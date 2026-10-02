from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class ExtractionResult:
    engine: str
    engine_version: str
    output_dir: Path
    page_count: int
    middle_json_path: Path
    markdown_path: Path
    structured_content_path: Path

class MinerUUnavailable(RuntimeError):
    pass

def extract_with_mineru(
    source: Path,
    output_dir: Path,
    *,
    tier: str = "standard",
    ocr_mode: str = "auto",
    image_analysis: bool = True,
) -> ExtractionResult:
    """Run the supplied MinerU production parser and persist its native outputs.

    ModuleIQ deliberately keeps MinerU behind this boundary. The extractor remains
    responsible for OCR/layout/formula/table/figure recognition; Phase 6 converts
    the native middle representation into canonical ModuleIQ objects.
    """
    try:
        from mineru import __version__ as mineru_version
        from mineru.parser import parse
    except ImportError as exc:
        raise MinerUUnavailable(
            "MinerU is not installed. Install the document-engine dependency to process documents."
        ) from exc

    output_dir.mkdir(parents=True, exist_ok=True)
    result = parse(
        source,
        tier=tier,
        ocr_mode=ocr_mode,
        image_analysis=image_analysis,
    )

    middle_json_path = output_dir / "middle_json.json"
    markdown_path = output_dir / "markdown.md"
    structured_path = output_dir / "structured_content.json"
    middle_json_path.write_text(result.to_json(), encoding="utf-8")
    markdown_path.write_text(result.markdown(), encoding="utf-8")
    structured_path.write_text(
        json.dumps(result.structured_content(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Preserve MinerU's own asset materialization path rather than inventing a
    # second extraction implementation. This writes referenced images/figures.
    try:
        from mineru.parser.writer import FileBasedDataWriter
        result.save(FileBasedDataWriter(str(output_dir)))
    except Exception as exc:
        raise RuntimeError(f"MinerU parsed the document but asset materialization failed: {exc}") from exc

    return ExtractionResult(
        engine="mineru",
        engine_version=str(mineru_version),
        output_dir=output_dir,
        page_count=len(result.pages),
        middle_json_path=middle_json_path,
        markdown_path=markdown_path,
        structured_content_path=structured_path,
    )
