"""Contracts shared by application services and infrastructure adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GenerationResult:
    text: str
    model: str
    latency_seconds: float
    error: str | None = None


class TextGenerationClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, *, system_prompt: str | None = None) -> GenerationResult:
        """Generate text; report provider failures in the result."""
        raise NotImplementedError


@dataclass(frozen=True)
class ResearchHit:
    text: str
    source: str
    score: float
    chunk_id: str = ""


class ResearchRetriever(ABC):
    @abstractmethod
    def search(self, query: str, *, limit: int = 4) -> list[ResearchHit]:
        """Find research passages without exposing storage-specific objects."""
        raise NotImplementedError


class RecommendationEnhancer(ABC):
    @abstractmethod
    def enhance(self, original: str, user_data: dict[str, Any]) -> dict[str, Any]:
        """Return an enhanced recommendation and its research metadata."""
        raise NotImplementedError
