"""Recommendation engines reused by Celery and offline evaluation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

from ..ai.contracts import GenerationResult, RecommendationEnhancer, TextGenerationClient


@dataclass(frozen=True)
class RecommendationResult:
    text: str
    generation: GenerationResult
    rag_latency_seconds: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class RecommendationEngine(ABC):
    @abstractmethod
    def recommend(self, user_data, sleep_statistics, sleep_records,
                  *, system_prompt: str | None = None) -> RecommendationResult:
        raise NotImplementedError


class DirectRecommendationEngine(RecommendationEngine):
    def __init__(self, client: TextGenerationClient, *, prompt_builder=None):
        self.client = client
        self.prompt_builder = prompt_builder

    def recommend(self, user_data, sleep_statistics, sleep_records,
                  *, system_prompt: str | None = None) -> RecommendationResult:
        from ..prompts.prompts_templates import create_sleep_analysis_prompt, get_system_prompt

        builder = self.prompt_builder or create_sleep_analysis_prompt
        prompt = builder(user_data, sleep_statistics, sleep_records)
        generation = self.client.generate(
            prompt,
            system_prompt=get_system_prompt() if system_prompt is None else system_prompt,
        )
        return RecommendationResult(
            text=generation.text if generation.error is None else "",
            generation=generation,
        )


class RagRecommendationEngine(DirectRecommendationEngine):
    def __init__(self, client: TextGenerationClient, enhancer: RecommendationEnhancer,
                 *, prompt_builder=None):
        super().__init__(client, prompt_builder=prompt_builder)
        self.enhancer = enhancer

    def recommend(self, user_data, sleep_statistics, sleep_records,
                  *, system_prompt: str | None = None) -> RecommendationResult:
        result = super().recommend(
            user_data, sleep_statistics, sleep_records, system_prompt=system_prompt,
        )
        if not result.text.strip():
            return result
        context = {
            "age_months": float(user_data.get_age_months()),
            "gender": user_data.get_gender(),
            "weight": float(user_data.weight),
            "height": user_data.height,
        }
        start = perf_counter()
        try:
            metadata = self.enhancer.enhance(result.text, context)
        except Exception as exc:
            metadata = {"error": str(exc)}
        enhanced = metadata.get("enhanced")
        text = (enhanced if isinstance(enhanced, str) and enhanced.strip()
                and not metadata.get("error") else result.text)
        return RecommendationResult(
            text, result.generation, perf_counter() - start, metadata,
        )
