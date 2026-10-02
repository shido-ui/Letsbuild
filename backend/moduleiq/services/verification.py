from __future__ import annotations
from sqlalchemy import select
from sqlalchemy.orm import Session
from moduleiq.infrastructure.database.models import Block, Classification, DifficultyAssessment, Provenance, Question, ReviewItem, Verification
from moduleiq.services.ai.orchestrator import AIContext, AIOrchestrator, ContextItem
from moduleiq.services.ai.schemas import DifficultyOutput, VerificationOutput

LOW_CONFIDENCE_THRESHOLD = 0.65

def _question_source_context(db: Session, question: Question) -> AIContext:
    items = [ContextItem(question.text, ({"source_kind": "question", "source_id": question.id},))]
    if question.provenance_id:
        provenance = db.get(Provenance, question.provenance_id)
        if provenance and provenance.source_block_id:
            block = db.get(Block, provenance.source_block_id)
            if block and block.text:
                items.append(ContextItem(block.text, ({"source_kind": "block", "source_id": block.id, "page_id": block.page_id},)))
    for solution in question.solutions:
        items.append(ContextItem(f"Solution ({solution.solution_type}): {solution.body}", ({"source_kind": "question_solution", "source_id": solution.id},)))
    return AIContext(items=tuple(items), max_chars=24000)

def _review(db: Session, question: Question, reason: str) -> None:
    existing = db.scalar(select(ReviewItem).where(
        ReviewItem.knowledge_base_id == question.knowledge_base_id,
        ReviewItem.entity_type == "question",
        ReviewItem.entity_id == question.id,
        ReviewItem.reason == reason,
        ReviewItem.status == "open",
    ))
    if existing is None:
        db.add(ReviewItem(knowledge_base_id=question.knowledge_base_id, entity_type="question", entity_id=question.id, reason=reason, status="open"))

def assess_question(db: Session, question_id: str, orchestrator: AIOrchestrator) -> dict:
    question = db.get(Question, question_id)
    if question is None:
        raise ValueError("Question not found")
    context = _question_source_context(db, question)
    difficulty_result = orchestrator.assess_difficulty(context)
    difficulty = difficulty_result.output
    if not isinstance(difficulty, DifficultyOutput):
        raise TypeError("Difficulty schema mismatch")
    assessment = DifficultyAssessment(
        overall=difficulty.overall,
        reasoning_depth=difficulty.reasoning_depth,
        calculation_complexity=difficulty.calculation_complexity,
        conceptual_complexity=difficulty.conceptual_complexity,
        prerequisite_depth=difficulty.prerequisite_depth,
        metadata_json={
            "confidence": difficulty.confidence,
            "notes": difficulty.notes,
            "provider": difficulty_result.provider,
            "model": difficulty_result.model,
            "attempts": difficulty_result.attempts,
            "source_references": [r.model_dump() for r in difficulty.source_references],
        },
    )
    db.add(assessment)
    db.flush()
    question.difficulty_id = assessment.id
    classification_confidence = None
    if question.classification_id:
        classification = db.get(Classification, question.classification_id)
        classification_confidence = classification.confidence if classification else None
    confidence_values = [difficulty.confidence]
    if classification_confidence is not None:
        confidence_values.append(classification_confidence)
    assessment_confidence = min(confidence_values)
    if assessment_confidence < LOW_CONFIDENCE_THRESHOLD:
        _review(db, question, "low_confidence_assessment")
    verification_results = []
    for solution in question.solutions:
        verification_result = orchestrator.verify(AIContext(
            items=context.items + (ContextItem(
                f"Verify this {solution.solution_type} solution against the supplied source: {solution.body}",
                ({"source_kind": "solution", "source_id": solution.id},),
            ),),
            max_chars=24000,
        ))
        verification = verification_result.output
        if not isinstance(verification, VerificationOutput):
            raise TypeError("Verification schema mismatch")
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
        solution.verification_id = record.id
        solution.confidence = verification.confidence
        verification_results.append(verification)
        if verification.status != "verified" or verification.confidence < LOW_CONFIDENCE_THRESHOLD:
            _review(db, question, "verification_uncertain" if verification.status == "uncertain" else "verification_failed")
    if not question.solutions:
        _review(db, question, "missing_solution_for_verification")
    db.commit()
    review_required = (
        assessment_confidence < LOW_CONFIDENCE_THRESHOLD
        or any(item.status != "verified" or item.confidence < LOW_CONFIDENCE_THRESHOLD for item in verification_results)
        or not question.solutions
    )
    return {
        "question_id": question.id,
        "difficulty": difficulty.model_dump(),
        "assessment_confidence": assessment_confidence,
        "verification": [item.model_dump() for item in verification_results],
        "review_required": review_required,
    }
