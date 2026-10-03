from __future__ import annotations

import hashlib
import math
import struct
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.base import utc_now
from moduleiq.infrastructure.database.models import VectorEmbedding


@dataclass(frozen=True)
class VectorMatch:
    object_id: str
    object_kind: str
    score: float
    model_name: str


def _pack(values: list[float]) -> bytes:
    if not values:
        raise ValueError("Embedding cannot be empty")
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Embedding contains a non-finite value")
    return struct.pack(f"<{len(values)}f", *values)


def _unpack(payload: bytes, dimension: int) -> list[float]:
    expected = dimension * 4
    if len(payload) != expected:
        raise ValueError("Stored embedding has an invalid byte length")
    return list(struct.unpack(f"<{dimension}f", payload))


def _cosine(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Embedding dimensions do not match")
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return dot / (left_norm * right_norm)


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def upsert_embedding(
    db: Session,
    *,
    knowledge_base_id: str,
    object_id: str,
    object_kind: str,
    model_name: str,
    values: list[float],
    source_text: str,
) -> VectorEmbedding:
    payload = _pack(values)
    row = db.scalar(
        select(VectorEmbedding).where(
            VectorEmbedding.object_kind == object_kind,
            VectorEmbedding.object_id == object_id,
        )
    )
    now = utc_now()
    if row is None:
        row = VectorEmbedding(
            id=uuid.uuid4().hex,
            knowledge_base_id=knowledge_base_id,
            object_id=object_id,
            object_kind=object_kind,
            model_name=model_name,
            dimension=len(values),
            embedding=payload,
            content_hash=content_hash(source_text),
            created_at=now,
            updated_at=now,
        )
        db.add(row)
    else:
        row.knowledge_base_id = knowledge_base_id
        row.model_name = model_name
        row.dimension = len(values)
        row.embedding = payload
        row.content_hash = content_hash(source_text)
        row.updated_at = now
    db.flush()
    return row


def search_vectors(
    db: Session,
    *,
    knowledge_base_id: str,
    query: list[float],
    model_name: str,
    limit: int = 20,
    min_score: float = -1.0,
) -> list[VectorMatch]:
    if not query:
        return []
    rows = db.scalars(
        select(VectorEmbedding).where(
            VectorEmbedding.knowledge_base_id == knowledge_base_id,
            VectorEmbedding.model_name == model_name,
            VectorEmbedding.dimension == len(query),
        )
    ).all()
    matches = [
        VectorMatch(
            object_id=row.object_id,
            object_kind=row.object_kind,
            score=_cosine(query, _unpack(row.embedding, row.dimension)),
            model_name=row.model_name,
        )
        for row in rows
    ]
    matches = [match for match in matches if match.score >= min_score]
    matches.sort(key=lambda match: match.score, reverse=True)
    return matches[: max(1, min(limit, 100))]
