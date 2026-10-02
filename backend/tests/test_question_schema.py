from moduleiq.services.ai.schemas import QuestionsOutput

def test_question_output_contract():
    value = QuestionsOutput(questions=[{"text":"What is velocity?","question_type":"open_ended","options":[],"answer":"Rate of change of displacement","source_references":[{"source_kind":"block","source_id":"b1"}]}])
    assert value.questions[0].question_type == "open_ended"
