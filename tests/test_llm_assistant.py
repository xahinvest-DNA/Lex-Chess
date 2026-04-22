import unittest

from app.config import Settings
from app.services.llm import LLMAssistant, build_followup_input, extract_output_text


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


if __name__ == "__main__":
    unittest.main()
