from moduleiq.services.ai.orchestrator import AIContext, AIOrchestrator, ContextItem
from moduleiq.services.ai.provider import AIProvider, AIResponse
from moduleiq.services.ai.errors import ProviderTimeoutError

class FakeProvider(AIProvider):
    provider_type = 'fake'
    def __init__(self): self.calls, self.mode = 0, 'good'
    def test_connection(self): pass
    def classify(self, text):
        self.calls += 1
        if self.mode == 'malformed_once' and self.calls == 1: return AIResponse('fake', 'test', 'not json')
        return AIResponse('fake', 'test', '{"subject":"Physics","topic":"Mechanics","subtopic":"Kinematics","confidence":0.91,"source_references":[{"source_kind":"block","source_id":"b1"}]}')
    extract = classify
    solve = classify
    verify = classify
    summarize = classify
    generate_questions = classify
    def analyze_image(self, image, media_type): raise NotImplementedError

def test_structured_output_and_provenance():
    p = FakeProvider()
    r = AIOrchestrator(p).classify(AIContext((ContextItem('Newton laws', ({'source_kind':'block','source_id':'b1'},)),)))
    assert r.output.subject == 'Physics'
    assert r.output.source_references[0].source_id == 'b1'

def test_malformed_json_retries():
    p = FakeProvider(); p.mode = 'malformed_once'
    r = AIOrchestrator(p).classify(AIContext((ContextItem('text'),)))
    assert r.attempts == 2 and p.calls == 2

def test_cache_avoids_duplicate_call():
    p = FakeProvider(); o = AIOrchestrator(p); c = AIContext((ContextItem('same'),))
    o.classify(c); r = o.classify(c)
    assert p.calls == 1 and r.cached

def test_long_context_is_bounded():
    p = FakeProvider(); AIOrchestrator(p, context_chars=1000).classify(AIContext((ContextItem('x' * 5000),)))
    assert p.calls == 1

def test_provider_timeout_retries_then_raises():
    class T(FakeProvider):
        def classify(self, text): self.calls += 1; raise ProviderTimeoutError('timeout')
    try: AIOrchestrator(T(), max_attempts=2).classify(AIContext((ContextItem('x'),)))
    except ProviderTimeoutError: return
    assert False