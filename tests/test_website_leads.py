import json
import tempfile
import unittest
from pathlib import Path

from app.services.website_leads import WebsiteLeadStore


class WebsiteLeadStoreTests(unittest.TestCase):
    def test_find_by_request_id_merges_resend_crm_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir)
            leads_path = data_dir / "site-leads.jsonl"
            resend_path = data_dir / "site-leads-resend.jsonl"
            request_id = "request-1"

            leads_path.write_text(
                json.dumps(
                    {
                        "lead": {"requestId": request_id, "name": "Иван"},
                        "crm": {"leadId": None, "taskId": None, "error": "fetch failed"},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            resend_path.write_text(
                json.dumps(
                    {
                        "lead": {"requestId": request_id},
                        "crm": {"leadId": 15, "taskId": 17},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            event = WebsiteLeadStore(leads_path).find_by_request_id(request_id)

        self.assertIsNotNone(event)
        self.assertEqual(event["lead"]["name"], "Иван")
        self.assertEqual(event["crm"]["leadId"], 15)
        self.assertEqual(event["crm"]["taskId"], 17)


if __name__ == "__main__":
    unittest.main()
