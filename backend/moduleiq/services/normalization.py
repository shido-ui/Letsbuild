from __future__ import annotations

import json
import mimetypes
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.models import (
    Asset, Block, DocumentVersion, Equation, Page, Provenance, Section, Table,
    Diagram,
)

TITLE_TYPES={"doc_title","paragraph_title","title","heading","chapter","section"}
TEXT_TYPES={"text","ref_text","page_footnote","paragraph","list","index","code","algorithm"}
EQUATION_TYPES={"equation"}
TABLE_TYPES={"table"}
VISUAL_TYPES={"image","chart","figure","diagram"}

def _text(value: Any) -> str:
    if value is None: return ""
    if isinstance(value,str): return value
    if isinstance(value,(int,float,bool)): return str(value)
    if isinstance(value,list): return "".join(_text(v) for v in value)
    if isinstance(value,dict):
        if "content" in value: return _text(value["content"])
        if "text" in value: return _text(value["text"])
        if "value" in value: return _text(value["value"])
        return ""
    return ""

def _bbox(raw: dict[str,Any]) -> dict[str,float]|None:
    value=raw.get("bbox") or raw.get("box") or raw.get("rect")
    if isinstance(value,dict):
        keys=("x0","y0","x1","y1")
        if all(k in value for k in keys):
            return {k:float(value[k]) for k in keys}
    if isinstance(value,(list,tuple)) and len(value)>=4:
        return {"x0":float(value[0]),"y0":float(value[1]),"x1":float(value[2]),"y1":float(value[3])}
    return None

def _table_rows(content: Any) -> list[list[Any]]:
    if isinstance(content,dict):
        for key in ("rows","data","cells"):
            if key in content: return _table_rows(content[key])
    if isinstance(content,list):
        rows=[]
        for row in content:
            if isinstance(row,list): rows.append([_text(c) for c in row])
            elif isinstance(row,dict):
                cells=row.get("cells") or row.get("content")
                if isinstance(cells,list): rows.append([_text(c) for c in cells])
                else: rows.append([_text(row)])
            else: rows.append([_text(row)])
        return rows
    value=_text(content)
    return [[value]] if value else []

def _asset_path(extraction_dir: Path, raw: dict[str,Any]) -> Path|None:
    source=raw.get("image_source") or raw.get("image_path")
    if not isinstance(source,str) or not source: return None
    candidate=(extraction_dir/source).resolve()
    root=extraction_dir.resolve()
    try: candidate.relative_to(root)
    except ValueError: return None
    return candidate if candidate.is_file() else None

def normalize_middle_json(db: Session, version: DocumentVersion, middle_json_path: Path, extraction_dir: Path) -> dict[str,int]:
    payload=json.loads(middle_json_path.read_text(encoding="utf-8"))
    if not isinstance(payload,dict) or not isinstance(payload.get("pages"),list):
        raise ValueError("MinerU middle JSON must contain a pages array.")
    if db.scalar(select(Page.id).where(Page.document_version_id==version.id)):
        raise ValueError("Document version is already normalized; refusing to duplicate canonical objects.")

    layout_pages={}
    layout=(payload.get("extensions") or {}).get("docvortex_layout") or {}
    for item in layout.get("pages",[]) if isinstance(layout,dict) else []:
        if isinstance(item,dict) and isinstance(item.get("page_idx"),int): layout_pages[item["page_idx"]]=item

    root_section=Section(id=str(uuid.uuid4()),document_version_id=version.id,title=version.document.title or "Document",level=0)
    db.add(root_section); db.flush()
    counts={"pages":0,"blocks":0,"equations":0,"tables":0,"assets":0,"diagrams":0,"sections":1,"provenance":0}

    section_stack={0:root_section}
    for page_pos, page_raw in enumerate(payload["pages"]):
        if not isinstance(page_raw,dict): continue
        page_idx=int(page_raw.get("page_idx",page_pos))
        layout_info=layout_pages.get(page_idx,{})
        width=layout_info.get("width_pt") or page_raw.get("width") or page_raw.get("width_pt")
        height=layout_info.get("height_pt") or page_raw.get("height") or page_raw.get("height_pt")
        page=Page(id=str(uuid.uuid4()),document_version_id=version.id,page_number=page_idx+1,
                  width=float(width) if width is not None else None,
                  height=float(height) if height is not None else None,
                  metadata_json={"mineru_page_idx":page_idx,"raw_page":page_raw})
        db.add(page); db.flush(); counts["pages"]+=1

        for ordinal, raw in enumerate(page_raw.get("blocks",[]) or []):
            if not isinstance(raw,dict): continue
            block_type=str(raw.get("type") or "unknown")
            content=raw.get("content")
            text=_text(content)
            block=Block(id=str(uuid.uuid4()),page_id=page.id,block_type=block_type,ordinal=ordinal,
                        text=text or None,bbox_json=_bbox(raw),
                        metadata_json={"mineru_index":raw.get("index"),"raw_block":raw})
            db.add(block); db.flush(); counts["blocks"]+=1
            db.add(Provenance(id=str(uuid.uuid4()),source_kind="mineru",source_document_id=version.document_id,
                              source_page_id=page.id,source_block_id=block.id,
                              locator=f"page:{page_idx+1}/block:{raw.get('index',ordinal)}"))
            counts["provenance"]+=1

            if block_type in TITLE_TYPES and text.strip():
                level=int(raw.get("level") or 1)
                parent=section_stack.get(max(k for k in section_stack if k < level),root_section)
                section=Section(id=str(uuid.uuid4()),document_version_id=version.id,parent_id=parent.id,
                                title=text.strip()[:500],level=level)
                db.add(section); db.flush(); section_stack={k:v for k,v in section_stack.items() if k<level}; section_stack[level]=section; counts["sections"]+=1
            elif block_type in EQUATION_TYPES:
                latex=text.strip()
                if latex: db.add(Equation(id=str(uuid.uuid4()),page_id=page.id,latex=latex,source_text=text,metadata_json={"mineru_block_index":raw.get("index"),"raw_block":raw})); counts["equations"]+=1
            elif block_type in TABLE_TYPES:
                rows=_table_rows(content)
                if rows: db.add(Table(id=str(uuid.uuid4()),page_id=page.id,caption=text[:1000] if text else None,data_json=rows,metadata_json={"mineru_block_index":raw.get("index"),"raw_block":raw})); counts["tables"]+=1
            elif block_type in VISUAL_TYPES:
                asset_path=_asset_path(extraction_dir,raw)
                asset_id=None
                if asset_path:
                    data=asset_path.read_bytes()
                    import hashlib
                    digest=hashlib.sha256(data).hexdigest()
                    asset=Asset(id=str(uuid.uuid4()),storage_uri=str(asset_path),media_type=mimetypes.guess_type(asset_path.name)[0] or "application/octet-stream",sha256=digest,byte_size=len(data),metadata_json={"source":"mineru","relative_path":str(asset_path.relative_to(extraction_dir))})
                    db.add(asset); db.flush(); asset_id=asset.id; counts["assets"]+=1
                diagram=Diagram(id=str(uuid.uuid4()),page_id=page.id,caption=text[:1000] if text else None,asset_id=asset_id,metadata_json={"mineru_block_index":raw.get("index"),"raw_block":raw})
                db.add(diagram); counts["diagrams"]+=1
    db.flush()
    return counts
