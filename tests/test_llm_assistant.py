import unittest

from app.config import Settings
from app.services.llm import (
    LLMAssistant,
    NON_LEGAL_FALLBACK,
    build_followup_input,
    extract_output_text,
    is_legal_followup,
)


def build_settings(**overrides) -> Settings:
    values = {
        "TELEGRAM_BOT_TOKEN": "token",
        "BITRIX24_WEBHOOK_URL": "https://example.bitrix24.ru/rest/1/token",
        "BITRIX24_RESPONSIBLE_ID": 1,
    }
    values.update(overrides)
    return Settings(**values)


class LLMAssistantTests(unittest.TestCase):
    def test_disabled_without_flag(self) -> None:
        assistant = LLMAssistant(build_settings(OPENAI_API_KEY="test-key"))

        self.assertFalse(assistant.is_enabled)
        self.assertIn("выключен", assistant.status_text())

    def test_enabled_requires_flag_and_key(self) -> None:
        assistant = LLMAssistant(build_settings(LLM_ENABLED=True, OPENAI_API_KEY="test-key"))

        self.assertTrue(assistant.is_enabled)
        self.assertIn("gpt-5.2", assistant.status_text())

    def test_followup_input_contains_context_and_message(self) -> None:
        payload = build_followup_input(
            "Когда можно прислать документы?",
            {
                "practice_area": "Развод",
                "situation_summary": "Нужен развод через суд.",
                "preferred_time": "Завтра 10:00-12:00",
            },
        )

        content = payload[0]["content"]
        self.assertIn("Развод", content)
        self.assertIn("Когда можно прислать документы?", content)

    def test_followup_input_contains_recent_dialog_history(self) -> None:
        payload = build_followup_input(
            "На жену, машину я покупал до брака",
            {"practice_area": "Раздел имущества"},
            [
                {"role": "assistant", "content": "Квартира оформлена на кого?"},
                {"role": "user", "content": "Квартира на жену."},
            ],
        )

        content = payload[0]["content"]
        self.assertIn("Бот: Квартира оформлена на кого?", content)
        self.assertIn("Клиент: Квартира на жену.", content)

    def test_extract_output_text_supports_sdk_convenience_field(self) -> None:
        self.assertEqual(extract_output_text({"output_text": "Ответ"}), "Ответ")

    def test_extract_output_text_supports_raw_response_items(self) -> None:
        payload = {
            "output": [
                {
                    "content": [
                        {"type": "output_text", "text": "Первая часть."},
                        {"type": "output_text", "text": "Вторая часть."},
                    ]
                }
            ]
        }

        self.assertEqual(extract_output_text(payload), "Первая часть.\nВторая часть.")

    def test_is_legal_followup_detects_legal_message(self) -> None:
        result = is_legal_followup(
            "Мне никто не позвонил, когда со мной свяжется юрист?",
            {"practice_area": "Раздел имущества"},
        )

        self.assertTrue(result)

    def test_is_legal_followup_rejects_irrelevant_message(self) -> None:
        result = is_legal_followup(
            "Как приготовить суп",
            {"practice_area": "Раздел имущества", "situation_summary": "Спор по квартире"},
            [{"role": "assistant", "content": "Удобно ли принять звонок?"}],
        )

        self.assertFalse(result)

    def test_non_legal_fallback_is_business_only(self) -> None:
        self.assertIn("юридической заявке", NON_LEGAL_FALLBACK)


if __name__ == "__main__":
    unittest.main()
