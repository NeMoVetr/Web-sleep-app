import json
import re
from typing import Any

from sleep_tracking_app.ai_clients import GeminiClient
from sleep_tracking_app.contracts import TextGenerationClient
from sleep_tracking_app.prompts.prompts_templates import make_judge_prompt


def _extract_json_block(text: str) -> dict[str, Any] | None:
    """Вытащить первое JSON-подобное тело из текста."""
    try:
        match = re.search(r"\{(?:[^{}]|(?R))*\}", text, flags=re.DOTALL)
    except Exception:
        match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    raw = match.group()
    try:
        return json.loads(raw)
    except Exception:
        try:
            return json.loads(raw.replace("'", '"'))
        except Exception:
            return None


class SleepLLMJudge:
    """LLM-судья для оценивания ответа ассистента по сну."""

    def __init__(self, client: TextGenerationClient | None = None):
        self.client = client if client is not None else GeminiClient()

    def _make_prompt(self, user_data, sleep_stats, sleep_record, response_text: str) -> str:
        return make_judge_prompt(user_data, sleep_stats, sleep_record, response_text)

    def evaluate(self, user_data, sleep_stats, sleep_record, response_text: str) -> dict[str, Any] | None:
        """Вернёт dict с оценками или None при ошибке."""
        prompt = self._make_prompt(user_data, sleep_stats, sleep_record, response_text)
        result = self.client.generate(prompt)
        return _extract_json_block(result.text) if result.error is None else None
