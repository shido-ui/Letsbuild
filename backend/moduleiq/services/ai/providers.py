from __future__ import annotations
import json
from typing import Any
from urllib import request, error
from .errors import InvalidCredentialError, ProviderTimeoutError, ProviderUnavailableError
from .provider import AIProvider, AIResponse

class OpenAICompatibleProvider(AIProvider):
    provider_type="openai_compatible"
    def __init__(self, api_key: str, model: str, base_url: str="https://api.openai.com/v1", timeout: float=30):
        self.api_key,self.model,self.base_url,self.timeout=api_key,model,base_url.rstrip("/"),timeout
    def _call(self, prompt: str) -> AIResponse:
        payload=json.dumps({"model":self.model,"messages":[{"role":"user","content":prompt}]}).encode()
        req=request.Request(self.base_url+"/chat/completions",data=payload,headers={"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"})
        try:
            with request.urlopen(req,timeout=self.timeout) as res: data=json.load(res)
        except error.HTTPError as exc:
            if exc.code in (401,403): raise InvalidCredentialError("Provider rejected credentials") from exc
            raise ProviderUnavailableError(f"Provider HTTP {exc.code}") from exc
        except TimeoutError as exc: raise ProviderTimeoutError("Provider request timed out") from exc
        except OSError as exc: raise ProviderUnavailableError("Provider connection failed") from exc
        try: content=data["choices"][0]["message"]["content"]
        except (KeyError,IndexError,TypeError) as exc: raise ProviderUnavailableError("Provider returned an invalid response") from exc
        return AIResponse(self.provider_type,self.model,content,data)
    def test_connection(self): self._call("Reply with the single word OK.")
    def classify(self,text): return self._call("Classify this material. Return concise structured facts.\\n"+text)
    def extract(self,text): return self._call("Extract structured knowledge from this source.\\n"+text)
    def solve(self,text): return self._call("Solve the supplied question carefully.\\n"+text)
    def verify(self,text): return self._call("Verify the supplied answer and explain discrepancies.\\n"+text)
    def summarize(self,text): return self._call("Summarize the supplied material.\\n"+text)
    def generate_questions(self,text): return self._call("Generate study questions from this material.\\n"+text)
    def analyze_image(self,image,media_type): raise NotImplementedError("Image analysis is provider-specific and is added without changing the provider boundary.")

class GeminiProvider(OpenAICompatibleProvider):
    provider_type="gemini"
    def __init__(self, api_key: str, model: str="gemini-2.5-flash", timeout: float=30):
        # Gemini's native transport is intentionally isolated behind this provider boundary.
        super().__init__(api_key,model,"https://generativelanguage.googleapis.com/v1beta/openai",timeout)

class LocalModelProvider(OpenAICompatibleProvider):
    provider_type="local"
    def __init__(self, base_url: str, model: str, timeout: float=60):
        super().__init__(api_key="local",model=model,base_url=base_url,timeout=timeout)
