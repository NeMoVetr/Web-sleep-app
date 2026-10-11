"""Adapters exposing the same interface for the supported text providers."""

from time import perf_counter
from typing import Callable

from .contracts import GenerationResult, TextGenerationClient


class GeminiClient(TextGenerationClient):
    def __init__(self, generate_text: Callable[[str], str] | None = None):
        # Import on use so contracts and injected clients need no provider SDK.
        self._generate_text = generate_text

    def generate(self, prompt: str, *, system_prompt: str | None = None) -> GenerationResult:
        from ..prompts.baseline import MODEL_NAME, call_gemini

        start = perf_counter()
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        try:
            text = (self._generate_text or call_gemini)(full_prompt) or ""
            error = None if text.strip() else "Gemini returned no text"
        except Exception as exc:
            text, error = "", str(exc)
        return GenerationResult(text, MODEL_NAME, perf_counter() - start, error)


class GigaChatClient(TextGenerationClient):
    def generate(self, prompt: str, *, system_prompt: str | None = None) -> GenerationResult:
        from ..sleep_statistic.gigachat import get_answer

        start = perf_counter()
        try:
            text = get_answer(prompt, system_prompt=system_prompt) or ""
            error = None if text.strip() else "GigaChat returned no text"
        except Exception as exc:
            text, error = "", str(exc)
        return GenerationResult(text, "GigaChat", perf_counter() - start, error)
