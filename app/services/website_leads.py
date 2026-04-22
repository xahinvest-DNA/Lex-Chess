from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class WebsiteLeadStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.resend_path = path.with_name("site-leads-resend.jsonl")

    def find_by_request_id(self, request_id: str) -> dict[str, Any] | None:
        found = self._find_event(self.path, request_id)
        resend_event = self._find_event(self.resend_path, request_id)

        if found and resend_event:
            found["crm"] = {
                **found.get("crm", {}),
                **resend_event.get("crm", {}),
            }
            return found

        if resend_event and not found:
            return resend_event

        return found

    @staticmethod
    def _find_event(path: Path, request_id: str) -> dict[str, Any] | None:
        if not path.exists():
            return None

        found: dict[str, Any] | None = None
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue

                lead = event.get("lead", {})
                if lead.get("requestId") == request_id:
                    found = event

        return found


def extract_request_id(start_payload: str | None) -> str | None:
    if not start_payload:
        return None
    payload = start_payload.strip()
    if payload.startswith("lead_"):
        return payload.removeprefix("lead_")
    return None
