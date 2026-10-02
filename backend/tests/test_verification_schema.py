from moduleiq.services.ai.schemas import DifficultyOutput, VerificationOutput

def test_difficulty_contract():
    value = DifficultyOutput(overall=0.8, reasoning_depth=0.7, calculation_complexity=0.5, conceptual_complexity=0.9, prerequisite_depth=0.6, confidence=0.88, notes="Multi-step conceptual reasoning.")
    assert value.overall == 0.8
    assert 0 <= value.confidence <= 1

def test_verification_contract():
    value = VerificationOutput(status="uncertain", confidence=0.42, notes="The source does not fully establish the answer.")
    assert value.status == "uncertain"
