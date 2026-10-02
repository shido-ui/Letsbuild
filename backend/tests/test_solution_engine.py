from moduleiq.services.ai.schemas import SolutionOutput, VerificationOutput
from moduleiq.services.solution_engine import _similarity


def test_solution_outputs_are_distinct_and_comparable():
    assert _similarity("v = u + at", "The velocity follows v = u + at.") > 0.5


def test_solution_schemas_support_steps_and_verification():
    solution = SolutionOutput(answer="x=2", steps=["substitute", "solve"], confidence=0.9)
    verification = VerificationOutput(status="verified", confidence=0.9, notes="Matches source.")
    assert solution.steps
    assert verification.status == "verified"
