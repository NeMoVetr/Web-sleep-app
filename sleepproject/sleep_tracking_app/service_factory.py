"""Compose production services at application entry points."""

from .ai_clients import GeminiClient
from .recommendations import RagRecommendationEngine


def create_rag_service():
    from .rag.ollama_client import OllamaClient
    from .rag.rag_service import RagService
    from .rag.vector_db import SleepVectorDB

    return RagService(vector_db=SleepVectorDB(), ollama_client=OllamaClient())


def create_recommendation_engine() -> RagRecommendationEngine:
    return RagRecommendationEngine(GeminiClient(), create_rag_service())
