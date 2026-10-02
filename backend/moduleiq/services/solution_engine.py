from __future__ import annotations

import json
import re
from difflib import SequenceMatcher

from sqlalchemy import select
from sqlalchemy.orm import Session

from moduleiq.infrastructure.database.models import (
    AISolution, Block, Diagram, Equation, Provenance, Question,
    QuestionSolution, SourceSolution, Table, Verification,
)
from moduleiq.services.ai.orchestrator import AIContext, AIOrchestrator, ContextItem
from moduleiq.services.ai.schemas import SolutionOutput, VerificationOutput

_SOLUTION_RE = re.compile(r"^\s*(?:answer|solution|sol(?:ution)?|worked\s+solution)\s*[:.)-]?\s*(.*)$", re.I)


def _source_context(db: Session, question: Question) -> tuple[AIContext, list[dict]]:
    items = [ContextItem(question.text, ({"source_kind": "question", "source_id": question.id},))]
    related = []
    provenance = db.get(Provenance, question.provenance_id) if question.provenance_id else None
    if provenance and provenance.source_block_id:
        block = db.get(Block, provenance.source_block_id)
        if block:
            blocks = db.scalars(
                select(Block).where(Block.page_id == block.page_id).order_by(Block.ordinal)
            ).all()
            for candidate in blocks:
                if candidate.id == block.id:
                    continue
                match = _SOLUTION_RE.match(candidate.text or "")
                if match:
                    body = match.group(1).strip() or (candidate.text or "").strip()
                    if body:
                        related.append({"kind": "source_solution", "block_id": candidate.id, "page_id": candidate.page_id})
                        items.append(ContextItem(
                            f"Original source solution: {body}",
                            ({"source_kind": "source_solution", "source_id": candidate.id, "page_id": candidate.page_id},),
                        ))
                    break
            for equation in db.scalars(select(Equation).where(Equation.page_id == block.page_id)).all():
                related.append({"kind": "equation", "id": equation.id, "page_id": block.page_id})
                items.append(ContextItem(
                    f"Equation: {equation.latex}",
                    ({"source_kind": "equation", "source_id": equation.id, "page_id": block.page_id},),
                ))
            for table in db.scalars(select(Table).where(Table.page_id == block.page_id)).all():
                related.append({"kind": "table", "id": table.id, "page_id": block.page_id})
                items.append(ContextItem(
                    f"Table {table.caption or ''}: {json.dumps(table.data_json)}",
                    ({"source_kind": "table", "source_id": table.id, "page_id": block.page_id},),
                ))
            for diagram in db.scalars(select(Diagram).where(Diagram.page_id == block.page_id)).all():
                related.append({"kind": "diagram", "id": diagram.id, "page_id": block.page_id, "caption": diagram.caption})
                if diagram.caption:
                    items.append(ContextItem(
                        f"Related diagram: {diagram.caption}",
                        ({"source_kind": "diagram", "source_id": diagram.id, "page_id": block.page_id},),
                    ))
    return AIContext(items=tuple(items), max_chars=24000), related


def _find_source_solution(db: Session, question: Question) -> SourceSolution | None:
    provenance = db.get(Provenance, question.provenance_id) if question.provenance_id else None
    if not provenance or not provenance.source_block_id:
        return None
    block = db.get(Block, provenance.source_block_id)
    if not block:
        return None
    blocks = db.scalars(
        select(Block).where(Block.page_id == block.page_id, Block.ordinal > block.ordinal)
        .order_by(Block.ordinal)
    ).all()
    for candidate in blocks[:12]:
        match = _SOLUTION_RE.match(candidate.text or "")
        if not match:
            continue
        body = match.group(1).strip() or (candidate.text or "").strip()
        if not body:
            continue
        existing = db.scalar(
            select(SourceSolution).join(QuestionSolution).where(
                QuestionSolution.question_id == question.id,
                SourceSolution.source_page_id == candidate.page_id,
            )
        )
        if existing:
            return existing
        qs = QuestionSolution(question_id=question.id, solution_type="source", body=body, confidence=1.0)
        db.add(qs)
        db.flush()
        db.add(SourceSolution(
            question_solution_id=qs.id,
            source_page_id=candidate.page_id,
            metadata_json={"source_block_id": candidate.id, "extraction": "labelled_source_solution"},
        ))
        db.flush()
        return db.scalar(select(SourceSolution).where(SourceSolution.question_solution_id == qs.id))
    return None


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def generate_ai_solution(db: Session, question_id: str, orchestrator: AIOrchestrator, provider_id: str | None = None) -> dict:
    question = db.get(Question, question_id)
    if question is None:
        raise ValueError("Question not found")

    source_solution = _find_source_solution(db, question)
    context, related = _source_context(db, question)
    result = orchestrator.solve(context)
    output = result.output
    if not isinstance(output, SolutionOutput):
        raise TypeError("Solution schema mismatch")

    ai_solution = db.scalar(
        select(QuestionSolution).join(AISolution).where(
            QuestionSolution.question_id == question.id,
            QuestionSolution.solution_type == "ai",
        )
    )
    if ai_solution is None:
        ai_solution = QuestionSolution(
            question_id=question.id,
            solution_type="ai",
            body=output.answer,
            confidence=output.confidence,
        )
        db.add(ai_solution)
        db.flush()
    else:
        ai_solution.body = output.answer
        ai_solution.confidence = output.confidence

    ai_solution.metadata_json = {
        "steps": output.steps,
        "provider": result.provider,
        "model": result.model,
        "attempts": result.attempts,
        "source_references": [r.model_dump() for r in output.source_references],
        "related_objects": related,
    }

    if ai_solution.ai_solution is None:
        db.add(AISolution(
            question_solution_id=ai_solution.id,
            provider_id=provider_id,
            model_name=result.model,
        ))
    else:
        ai_solution.ai_solution.model_name = result.model

    verification = None
    try:
        verification_result = orchestrator.verify(AIContext(
            items=context.items + (
                ContextItem(
                    f"Verify this AI-generated solution against the source context: {output.answer}",
                    ({"source_kind": "ai_solution", "source_id": ai_solution.id},),
                ),
            ),
            max_chars=24000,
        ))
        verification = verification_result.output
        if isinstance(verification, VerificationOutput):
            record = Verification(
                status=verification.status,
                verifier_type="ai",
                confidence=verification.confidence,
                notes=verification.notes,
                metadata_json={
                    "provider": verification_result.provider,
                    "model": verification_result.model,
                    "attempts": verification_result.attempts,
                    "source_references": [r.model_dump() for r in verification.source_references],
                },
            )
            db.add(record)
            db.flush()
            ai_solution.verification_id = record.id
            ai_solution.confidence = min(output.confidence, verification.confidence)
    except Exception as exc:
        ai_solution.metadata_json["verification_error"] = str(exc)

    db.commit()
    source_body = next((s.body for s in question.solutions if s.solution_type == "source"), None)
    return {
        "question_id": question.id,
        "source_solution": {
            "available": source_solution is not None,
            "solution_id": source_solution.question_solution_id if source_solution else None,
            "body": source_body,
        },
        "ai_solution": {
            "solution_id": ai_solution.id,
            "answer": ai_solution.body,
            "steps": output.steps,
            "confidence": ai_solution.confidence,
            "provider": result.provider,
            "model": result.model,
            "related_objects": related,
            "verification": verification.model_dump() if isinstance(verification, VerificationOutput) else None,
        },
    }
