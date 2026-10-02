from __future__ import annotations
import hashlib, json, re, time
from dataclasses import dataclass
from threading import Lock
from typing import Any
from pydantic import BaseModel, ValidationError
from .errors import AIProviderError, ProviderTimeoutError
from .provider import AIProvider
from .schemas import AIExecutionResult, ClassificationOutput, ExtractionOutput, SolutionOutput, VerificationOutput, SummaryOutput, QuestionsOutput

@dataclass(frozen=True)
class ContextItem:
    text: str
    source_references: tuple[dict[str, Any], ...] = ()

@dataclass(frozen=True)
class AIContext:
    items: tuple[ContextItem, ...]
    max_chars: int = 24000
    def render(self) -> str:
        parts, used = [], 0
        for index, item in enumerate(self.items, 1):
            refs = json.dumps(list(item.source_references), separators=(',', ':'))
            chunk = f'[SOURCE {index}]\n{item.text}\n[REFERENCES]{refs}'
            if used + len(chunk) > self.max_chars:
                remaining = self.max_chars - used
                if remaining > 200: parts.append(chunk[:remaining])
                break
            parts.append(chunk); used += len(chunk)
        return '\n\n'.join(parts)

class _TTLCache:
    def __init__(self, max_items=128, ttl_seconds=900):
        self.max_items, self.ttl_seconds = max_items, ttl_seconds
        self._data, self._lock = {}, Lock()
    def get(self, key):
        with self._lock:
            value = self._data.get(key)
            if not value: return None
            if time.monotonic() - value[0] > self.ttl_seconds:
                self._data.pop(key, None); return None
            return value[1].model_copy(update={'cached': True})
    def put(self, key, value):
        with self._lock:
            if len(self._data) >= self.max_items:
                self._data.pop(min(self._data, key=lambda k: self._data[k][0]), None)
            self._data[key] = (time.monotonic(), value)

class AIOrchestrator:
    def __init__(self, provider: AIProvider, *, max_attempts=3, context_chars=24000, cache=None):
        self.provider, self.max_attempts = provider, max(1, max_attempts)
        self.context_chars, self.cache = max(1000, context_chars), cache or _TTLCache()
    def _cache_key(self, operation, context):
        return hashlib.sha256((operation + '\\x00' + context.render()).encode()).hexdigest()
    @staticmethod
    def _extract_json(content):
        text = content.strip()
        if text.startswith('```'):
            text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.I)
            text = re.sub(r'\s*```$', '', text)
        try: return json.loads(text)
        except json.JSONDecodeError:
            starts = [p for p in (text.find('{'), text.find('[')) if p >= 0]
            if not starts: raise
            start, end = min(starts), max(text.rfind('}'), text.rfind(']'))
            if end <= start: raise
            return json.loads(text[start:end + 1])
    def _run(self, operation, context, schema, call):
        context = AIContext(context.items, min(context.max_chars, self.context_chars))
        key = self._cache_key(operation, context)
        cached = self.cache.get(key)
        if cached: return cached
        prompt = self._prompt(operation, schema, context)
        last_error, previous = None, ''
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = call(prompt); previous = response.content
                output = schema.model_validate(self._extract_json(response.content))
                result = AIExecutionResult(operation=operation, provider=response.provider, model=response.model, attempts=attempt, output=output, source_references=getattr(output, 'source_references', []))
                self.cache.put(key, result); return result
            except (json.JSONDecodeError, ValidationError) as exc:
                last_error = exc
                if attempt < self.max_attempts: prompt = self._repair_prompt(operation, schema, previous)
            except ProviderTimeoutError as exc:
                last_error = exc
                if attempt >= self.max_attempts: raise
            except AIProviderError as exc:
                last_error = exc
                if attempt >= self.max_attempts: raise
        raise AIProviderError(f'AI operation failed after {self.max_attempts} attempts: {last_error}')
    @staticmethod
    def _prompt(operation, schema, context):
        return ('You are a ModuleIQ structured knowledge service.\n'
                f'Operation: {operation}.\n'
                'Use only the supplied source context. Do not invent source references. Return JSON only, matching the schema exactly.\n'
                f'Schema: {json.dumps(schema.model_json_schema(), separators=(",", ":"))}\n\nContext:\n{context.render()}')
    @staticmethod
    def _repair_prompt(operation, schema, previous):
        return (f'Repair the previous response for ModuleIQ operation {operation!r}. Return JSON only and match this schema exactly.\n'
                f'Schema: {json.dumps(schema.model_json_schema(), separators=(",", ":"))}\nPrevious response:\n{previous}')
    def classify(self, context): return self._run('classify', context, ClassificationOutput, self.provider.classify)
    def extract(self, context): return self._run('extract', context, ExtractionOutput, self.provider.extract)
    def solve(self, context): return self._run('solve', context, SolutionOutput, self.provider.solve)
    def verify(self, context): return self._run('verify', context, VerificationOutput, self.provider.verify)
    def summarize(self, context): return self._run('summarize', context, SummaryOutput, self.provider.summarize)
    def generate_questions(self, context): return self._run('generate_questions', context, QuestionsOutput, self.provider.generate_questions)