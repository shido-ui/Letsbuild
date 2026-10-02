from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class AIResponse:
    provider: str
    model: str
    content: str
    raw: Any = None

class AIProvider(ABC):
    provider_type: str
    @abstractmethod
    def test_connection(self) -> None: ...
    @abstractmethod
    def classify(self, text: str) -> AIResponse: ...
    @abstractmethod
    def extract(self, text: str) -> AIResponse: ...
    @abstractmethod
    def solve(self, text: str) -> AIResponse: ...
    @abstractmethod
    def verify(self, text: str) -> AIResponse: ...
    @abstractmethod
    def summarize(self, text: str) -> AIResponse: ...
    @abstractmethod
    def generate_questions(self, text: str) -> AIResponse: ...
    @abstractmethod
    def analyze_image(self, image: bytes, media_type: str) -> AIResponse: ...
