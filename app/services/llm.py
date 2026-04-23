from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import Settings


logger = logging.getLogger(__name__)

NON_LEGAL_FALLBACK = (
    "Помогу только по вашей юридической заявке. "
    "Если хотите, напишите, что именно нужно по делу: сроки связи, документы, обстоятельства спора или уточнение по ситуации."
)


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

    async def answer_followup(
        self,
        user_message: str,
        answers: dict[str, Any],
        history: list[dict[str, str]] | None = None,
    ) -> str | None:
        if not self.is_enabled:
            return None

        if not is_legal_followup(user_message, answers, history or []):
            return NON_LEGAL_FALLBACK

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
                        "input": build_followup_input(user_message, answers, history or []),
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
        f"Ты живой и внимательный координатор юридической компании {settings.law_firm_name}. "
        "Клиент уже оставил заявку, а вся переписка попадает юристу в CRM. "
        "Отвечай как человек в чате: тепло, спокойно, без канцелярита и без повторяющихся дисклеймеров. "
        "Не называй себя AI, моделью, роботом или предварительным AI-ответом. "
        "Ты общаешься только по юридической заявке клиента. "
        "Если сообщение не относится к юридическому вопросу, заявке, документам, срокам, записи на консультацию или связи с юристом, "
        "не поддерживай свободную беседу и не отвечай по посторонней теме. "
        "В таком случае вежливо верни разговор к делу одной короткой фразой. "
        "Не начинай каждый ответ одинаково. Не повторяй постоянно, что юрист все увидит: это можно сказать только если действительно уместно. "
        "Учитывай предыдущие сообщения в этом Telegram-диалоге и продолжай разговор, а не начинай квалификацию заново. "
        "Если клиент сообщает новый факт, коротко подтверди, что понял, и объясни, почему этот факт важен. "
        "Если нужен следующий шаг, задай максимум 1-2 точных вопроса или попроси 1-3 конкретных документа. "
        "Не перегружай клиента длинными списками документов в каждом ответе. "
        "Не обещай результат, не давай гарантий, не называй точную стоимость и не выдавай ответ за полноценную юридическую консультацию. "
        "Не составляй окончательную правовую позицию и не придумывай факты. "
        "Ответ должен быть до 650 символов."
    )


def build_followup_input(
    user_message: str,
    answers: dict[str, Any],
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    context_lines = [
        f"Направление: {answers.get('practice_area') or '-'}",
        f"Ситуация: {answers.get('situation_summary') or '-'}",
        f"Срочность: {answers.get('urgency') or '-'}",
        f"Ключевые факты: {answers.get('financial_or_family_context') or '-'}",
        f"Документы: {answers.get('documents_ready') or '-'}",
        f"Регион: {answers.get('region') or '-'}",
        f"Предпочтительное время: {answers.get('preferred_time') or '-'}",
    ]
    history_lines = []
    for item in (history or [])[-8:]:
        role = "Клиент" if item.get("role") == "user" else "Бот"
        content = str(item.get("content") or "").strip()
        if content:
            history_lines.append(f"{role}: {content}")

    return [
        {
            "role": "user",
            "content": (
                "Данные заявки:\n"
                + "\n".join(context_lines)
                + "\n\nПоследние сообщения в Telegram:\n"
                + ("\n".join(history_lines) if history_lines else "-")
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


LEGAL_MARKERS = [
    "юрист",
    "заявк",
    "дел",
    "суд",
    "развод",
    "имуществ",
    "банкрот",
    "долг",
    "ипотек",
    "квартир",
    "машин",
    "авто",
    "документ",
    "егрн",
    "птс",
    "договор",
    "срок",
    "позвон",
    "связ",
    "консульта",
    "пристав",
    "кредит",
    "мфо",
    "алимент",
    "супруг",
    "супруга",
    "брак",
    "муж",
    "жена",
    "раздел",
    "лид",
]


def is_legal_followup(
    user_message: str,
    answers: dict[str, Any],
    history: list[dict[str, str]] | None = None,
) -> bool:
    current_text = user_message.lower()
    if any(marker in current_text for marker in LEGAL_MARKERS):
        return True

    short_message = len(current_text.split()) <= 8
    if short_message:
        return False

    text = " ".join(
        [
            user_message,
            str(answers.get("practice_area") or ""),
            str(answers.get("situation_summary") or ""),
            str(answers.get("financial_or_family_context") or ""),
            " ".join(str(item.get("content") or "") for item in (history or [])[-4:]),
        ]
    ).lower()
    return any(marker in text for marker in LEGAL_MARKERS)
