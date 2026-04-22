import unittest

from app.config import Settings
from app.integrations.bitrix24 import Bitrix24Client
from app.services.intake import IntakeCoordinator
from app.storage.sqlite import SQLiteStorage


class DummyBot:
    async def send_message(self, *args, **kwargs):
        return None


def build_settings() -> Settings:
    return Settings(
        TELEGRAM_BOT_TOKEN="token",
        BITRIX24_WEBHOOK_URL="https://example.bitrix24.ru/rest/1/token",
        BITRIX24_RESPONSIBLE_ID=1,
    )


class IntakePrefillTests(unittest.TestCase):
    def test_next_missing_step_skips_prefilled_website_answers(self) -> None:
        settings = build_settings()
        coordinator = IntakeCoordinator(
            settings=settings,
            storage=SQLiteStorage(settings.db_path),
            bitrix_client=Bitrix24Client(settings),
            bot=DummyBot(),
        )
        answers = {
            "practice_area": coordinator.questions[0].options[0],
            "client_type": coordinator.questions[1].options[0],
            "situation_summary": "Есть заявка с сайта с уже заполненным описанием.",
            "urgency": coordinator.questions[3].options[0],
            "consultation_format": coordinator.questions[9].options[0],
            "full_name": "Иван Иванов",
            "phone": "+79000000000",
            "lead_source": coordinator.questions[15].options[0],
        }

        self.assertEqual(coordinator._next_missing_step(0, answers), 4)
        answers["deadline_details"] = "Нет срочного дедлайна"
        self.assertEqual(coordinator._next_missing_step(5, answers), 5)


if __name__ == "__main__":
    unittest.main()
