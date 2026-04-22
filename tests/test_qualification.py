import unittest

from app.config import Settings
from app.domain.models import LeadFit, LeadStatus
from app.domain.qualification import evaluate_lead


def build_settings() -> Settings:
    return Settings(
        TELEGRAM_BOT_TOKEN="token",
        BITRIX24_WEBHOOK_URL="https://example.bitrix24.ru/rest/1/token",
        BITRIX24_RESPONSIBLE_ID=1,
    )


class QualificationTests(unittest.TestCase):
    def test_hot_lead_scores_high(self) -> None:
        settings = build_settings()
        result = evaluate_lead(
            {
                "client_type": "Физическое лицо",
                "practice_area": "Банкротство физического лица",
                "urgency": "Сегодня",
                "deadline_details": "Завтра суд, нужно срочно подготовить позицию.",
                "financial_or_family_context": "Долг по кредитам и МФО, есть приставы.",
                "region": "Москва",
                "documents_ready": "Да, все основные",
                "consultation_terms_ack": "Да, подходит",
                "consultation_format": "Онлайн-встреча",
            },
            settings,
        )
        self.assertIs(result.status, LeadStatus.HOT)
        self.assertIs(result.fit, LeadFit.TARGET)
        self.assertGreaterEqual(result.score, 70)

    def test_low_fit_lead_drops_score(self) -> None:
        settings = build_settings()
        result = evaluate_lead(
            {
                "client_type": "Компания",
                "practice_area": "Нужно уточнить направление",
                "urgency": "Пока просто консультация",
                "deadline_details": "Нет срочного дедлайна",
                "financial_or_family_context": "Общий вопрос без документов.",
                "region": "Другая страна",
                "documents_ready": "Пока нет",
                "consultation_terms_ack": "Нужно сначала уточнить условия",
                "consultation_format": "Telegram",
            },
            settings,
        )
        self.assertIn(result.status, {LeadStatus.REVIEW, LeadStatus.LOW_FIT})

    def test_non_target_lead_routes_to_junk(self) -> None:
        settings = build_settings()
        result = evaluate_lead(
            {
                "client_type": "Физическое лицо",
                "practice_area": "Банкротство физического лица",
                "urgency": "Сегодня",
                "deadline_details": "Суд завтра.",
                "financial_or_family_context": "Банкротство ООО, арбитраж, договор поставки.",
                "situation_summary": "Нужно банкротство ООО и арбитражный спор по договору поставки.",
                "region": "Москва",
                "documents_ready": "Частично",
                "consultation_terms_ack": "Да, подходит",
                "consultation_format": "Телефон",
            },
            settings,
        )

        self.assertIs(result.fit, LeadFit.NON_TARGET)
        self.assertIs(result.status, LeadStatus.LOW_FIT)
        self.assertEqual(result.bitrix_status_id, "JUNK")


if __name__ == "__main__":
    unittest.main()
