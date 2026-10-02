from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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

def extract_with_mineru(source: Path, output_dir: Path, *, tier: str="standard", ocr_mode: str="auto", image_analysis: bool=True)->ExtractionResult:
    """Run the supplied MinerU parser and persist its native result package."""
    try:
        from mineru import __version__ as mineru_version
        from mineru.parser import parse
        from mineru.parser.writer import FileBasedDataWriter
    except ImportError as exc:
        raise MinerUUnavailable("MinerU is not installed. Install the document-engine dependency to process documents.") from exc

    output_dir.mkdir(parents=True,exist_ok=True)
    result=parse(source,tier=tier,ocr_mode=ocr_mode,image_analysis=image_analysis)
    result.save(FileBasedDataWriter(str(output_dir)))
    middle_json_path=output_dir/"middle_json.json"
    markdown_path=output_dir/"markdown.md"
    structured_path=output_dir/"structured_content.json"
    if not (middle_json_path.exists() and markdown_path.exists() and structured_path.exists()):
        raise RuntimeError("MinerU completed but did not produce its required native result package.")
    return ExtractionResult(
        engine="mineru",
        engine_version=str(mineru_version),
        output_dir=output_dir,
        page_count=len(result.pages),
        middle_json_path=middle_json_path,
        markdown_path=markdown_path,
        structured_content_path=structured_path,
    )
