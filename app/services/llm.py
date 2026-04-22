from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import Settings


logger = logging.getLogger(__name__)


class LLMAssistant:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def is_enabled(self) -> bool:
        return bool(self.settings.llm_enabled and self.settings.openai_api_key)

    def status_text(self) -> str:
        if not self.settings.llm_enabled:
            return "LLM выключен: LLM_ENABLED=false."
        if not self.settings.openai_api_key:
            return "LLM включен, но не задан OPENAI_API_KEY."
        return f"LLM включен. Модель: {self.settings.openai_model}."

    async def answer_followup(self, user_message: str, answers: dict[str, Any]) -> str | None:
        if not self.is_enabled:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.settings.openai_timeout_seconds) as client:
                response = await client.post(
                    "https://api.openai.com/v1/responses",
                    headers={
                        "Authorization": f"Bearer {self.settings.openai_api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.settings.openai_model,
                        "instructions": build_followup_instructions(self.settings),
                        "input": build_followup_input(user_message, answers),
                        "max_output_tokens": self.settings.openai_max_output_tokens,
                    },
                )
                response.raise_for_status()
        except Exception:
            logger.exception("LLM follow-up request failed")
            return None

        text = extract_output_text(response.json()).strip()
        return text or None


def build_followup_instructions(settings: Settings) -> str:
    return (
        f"Ты ассистент юридической компании {settings.law_firm_name}. "
        "Отвечай клиенту на русском языке кратко, спокойно и профессионально. "
        "Контекст: клиент уже оставил заявку, юрист увидит переписку в CRM. "
        "Не обещай результат, не давай гарантий, не называй точную стоимость и не выдавай ответ за полноценную юридическую консультацию. "
        "Можно: объяснить общий следующий шаг, попросить недостающие документы или уточнения, помочь структурировать вопрос. "
        "Нельзя: составлять окончательную правовую позицию, ссылаться на несуществующие нормы, придумывать факты. "
        "Если данных недостаточно, задай 1-2 уточняющих вопроса. "
        "Ответ должен быть до 900 символов."
    )


def build_followup_input(user_message: str, answers: dict[str, Any]) -> list[dict[str, str]]:
    context_lines = [
        f"Направление: {answers.get('practice_area') or '-'}",
        f"Ситуация: {answers.get('situation_summary') or '-'}",
        f"Срочность: {answers.get('urgency') or '-'}",
        f"Ключевые факты: {answers.get('financial_or_family_context') or '-'}",
        f"Документы: {answers.get('documents_ready') or '-'}",
        f"Регион: {answers.get('region') or '-'}",
        f"Предпочтительное время: {answers.get('preferred_time') or '-'}",
    ]
    return [
        {
            "role": "user",
            "content": (
                "Данные заявки:\n"
                + "\n".join(context_lines)
                + "\n\nНовое сообщение клиента:\n"
                + user_message
            ),
        }
    ]


def extract_output_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]

    chunks: list[str] = []
    for item in payload.get("output", []) or []:
        for content in item.get("content", []) or []:
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks)
