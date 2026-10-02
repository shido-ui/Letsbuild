from moduleiq.services.ai.schemas import KnowledgeOutput

def test_knowledge_schema_accepts_domain_agnostic_hierarchy():
    value = KnowledgeOutput(subject="Physics", section="Mechanics", chapter="Kinematics", confidence=0.9, topics=[{"name":"Motion","subtopics":[{"name":"Velocity","concepts":["displacement","speed"]}]}], prerequisites=[{"prerequisite":"displacement","dependent":"speed","strength":0.7}])
    assert value.topics[0].subtopics[0].concepts == ["displacement", "speed"]
    assert value.prerequisites[0].strength == 0.7
