import asyncio
import base64
import unittest
from unittest.mock import AsyncMock

from app.config import Settings
from app.domain.models import LeadStatus, QualificationResult
from app.integrations.bitrix24 import Bitrix24Client


def build_settings() -> Settings:
    return Settings(
        TELEGRAM_BOT_TOKEN="token",
        BITRIX24_WEBHOOK_URL="https://example.bitrix24.ru/rest/1/token",
        BITRIX24_RESPONSIBLE_ID=7,
        BITRIX24_CREATOR_ID=3,
    )


class BitrixPayloadTests(unittest.TestCase):
    def test_lead_payload_uses_universal_crm_method_shape(self) -> None:
        settings = build_settings()
        client = Bitrix24Client(settings)
        payload = client.build_lead_payload(
            chat_id=55,
            answers={
                "practice_area": "Семейное право",
                "full_name": "Иван Петров",
                "client_type": "Физлицо",
                "phone": "+7 999 111-22-33",
                "email": "[email protected]",
            },
            qualification=QualificationResult(
                status=LeadStatus.QUALIFIED,
                score=61,
                manager_priority="normal",
                recommended_response_hours=4,
                tags=["practice-fit"],
                rationale=["Запрос подходит фирме."],
            ),
        )
        self.assertEqual(payload["entityTypeId"], 1)
        self.assertEqual(payload["fields"]["sourceDescription"], "Telegram legal intake bot")
        self.assertEqual(payload["fields"]["fm"][0]["typeId"], "PHONE")
        asyncio.run(client.close())

    def test_task_payload_links_bitrix_lead(self) -> None:
        settings = build_settings()
        client = Bitrix24Client(settings)
        payload = client.build_task_payload(
            lead_id=101,
            answers={
                "practice_area": "Трудовые споры",
                "full_name": "Мария Иванова",
            },
            qualification=QualificationResult(
                status=LeadStatus.HOT,
                score=80,
                manager_priority="high",
                recommended_response_hours=1,
                tags=["urgent"],
                rationale=["Срочный кейс."],
            ),
        )
        self.assertEqual(payload["fields"]["RESPONSIBLE_ID"], 7)
        self.assertEqual(payload["fields"]["UF_CRM_TASK"], ["L_101"])
        asyncio.run(client.close())

    def test_timeline_comment_can_attach_files(self) -> None:
        async def run_test() -> None:
            settings = build_settings()
            client = Bitrix24Client(settings)
            client.call = AsyncMock(return_value=42)

            result = await client.add_timeline_comment(
                lead_id=101,
                comment="Документ клиента",
                files=[("passport.jpg", b"file-bytes")],
            )

            self.assertEqual(result, 42)
            method, payload = client.call.await_args.args
            self.assertEqual(method, "crm.timeline.comment.add")
            self.assertEqual(payload["fields"]["ENTITY_ID"], 101)
            self.assertEqual(
                payload["fields"]["FILES"],
                [["passport.jpg", base64.b64encode(b"file-bytes").decode("ascii")]],
            )
            await client.close()

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
