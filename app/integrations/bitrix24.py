from __future__ import annotations

import base64
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.config import Settings
from app.domain.models import BitrixSubmissionResult, LeadStatus, QualificationResult
from app.services.formatters import build_case_snapshot


class Bitrix24APIError(RuntimeError):
    pass


class Bitrix24Client:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.AsyncClient(timeout=20.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def submit_intake(
        self,
        chat_id: int,
        answers: dict[str, str],
        qualification: QualificationResult,
    ) -> BitrixSubmissionResult:
        result = BitrixSubmissionResult()

        try:
            existing_lead_id = _int_or_none(answers.get("website_bitrix_lead_id"))
            if existing_lead_id:
                result.lead_id = existing_lead_id
                task_payload = self.build_task_payload(existing_lead_id, answers, qualification)
                task_response = await self.call("tasks.task.add", task_payload)
                result.task_id = self._extract_task_id(task_response)
                await self._try_start_task(result.task_id)

                timeline_payload = self.build_timeline_comment_payload(existing_lead_id, answers, qualification)
                timeline_response = await self.call("crm.timeline.comment.add", timeline_payload)
                result.timeline_comment_id = int(timeline_response)
                return result

            lead_payload = self.build_lead_payload(chat_id, answers, qualification)
            lead_response = await self.call("crm.item.add", lead_payload)
            result.lead_id = int(lead_response["item"]["id"])

            task_payload = self.build_task_payload(result.lead_id, answers, qualification)
            task_response = await self.call("tasks.task.add", task_payload)
            result.task_id = self._extract_task_id(task_response)
            await self._try_start_task(result.task_id)

            timeline_payload = self.build_timeline_comment_payload(result.lead_id, answers, qualification)
            timeline_response = await self.call("crm.timeline.comment.add", timeline_payload)
            result.timeline_comment_id = int(timeline_response)
        except Exception as exc:  # pragma: no cover - exercised through call-site fallbacks
            result.error_message = str(exc)

        return result

    async def call(self, method: str, payload: dict[str, Any]) -> Any:
        url = f"{self.settings.bitrix24_webhook_url.rstrip('/')}/{method}"
        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            raise Bitrix24APIError(f"{data['error']}: {data.get('error_description', '')}".strip())
        return data["result"]

    async def add_timeline_comment(
        self,
        lead_id: int,
        comment: str,
        files: list[tuple[str, bytes]] | None = None,
    ) -> int | None:
        fields: dict[str, Any] = {
            "ENTITY_ID": lead_id,
            "ENTITY_TYPE": "lead",
            "COMMENT": comment,
        }
        if files:
            fields["FILES"] = [
                [file_name, base64.b64encode(content).decode("ascii")]
                for file_name, content in files
            ]

        response = await self.call(
            "crm.timeline.comment.add",
            {"fields": fields},
        )
        return int(response) if response else None

    async def _try_start_task(self, task_id: int | None) -> None:
        if not task_id:
            return
        try:
            await self.call("tasks.task.start", {"taskId": task_id})
        except Exception:
            return

    def build_lead_payload(
        self,
        chat_id: int,
        answers: dict[str, str],
        qualification: QualificationResult,
    ) -> dict[str, Any]:
        first_name, last_name = _split_name(answers.get("full_name", ""))
        fields: dict[str, Any] = {
            "title": f"{answers.get('practice_area', 'Юр. запрос')} | {answers.get('full_name', 'Без имени')}",
            "name": first_name,
            "lastName": last_name,
            "sourceId": self.settings.bitrix24_source_id,
            "sourceDescription": "Telegram legal intake bot",
            "assignedById": qualification.responsible_id or self.settings.bitrix24_responsible_id,
            "comments": build_case_snapshot(answers, qualification),
            "statusDescription": self._build_status_description(answers, qualification),
            "statusId": qualification.bitrix_status_id or self.settings.bitrix24_target_status_id,
            "originatorId": "telegram-bot",
            "originId": str(chat_id),
            "utmSource": "telegram",
            "utmMedium": "bot",
            "companyTitle": answers.get("client_type") if answers.get("client_type") == "Компания" else None,
            "fm": [
                {
                    "typeId": "PHONE",
                    "valueType": "WORK",
                    "value": answers.get("phone", ""),
                }
            ],
        }
        email = answers.get("email", "")
        if email and email.lower() != "нет":
            fields["fm"].append(
                {
                    "typeId": "EMAIL",
                    "valueType": "WORK",
                    "value": email,
                }
            )
        return {
            "entityTypeId": self.settings.bitrix24_entity_type_id,
            "fields": fields,
        }

    def build_task_payload(
        self,
        lead_id: int,
        answers: dict[str, str],
        qualification: QualificationResult,
    ) -> dict[str, Any]:
        deadline = datetime.now().astimezone() + timedelta(hours=qualification.recommended_response_hours)
        priority = 2 if qualification.status is LeadStatus.HOT else 1
        return {
            "fields": {
                "TITLE": (
                    f"[{answers.get('preferred_time', 'слот не выбран')}] "
                    f"[{qualification.manager_priority}] "
                    f"{answers.get('practice_area', 'Юр. лид')} | {answers.get('full_name', 'Без имени')}"
                ),
                "DESCRIPTION": build_case_snapshot(answers, qualification),
                "CREATED_BY": self.settings.creator_id,
                "RESPONSIBLE_ID": qualification.responsible_id or self.settings.bitrix24_responsible_id,
                "PRIORITY": priority,
                "DEADLINE": deadline.replace(microsecond=0).isoformat(),
                "UF_CRM_TASK": [f"L_{lead_id}"],
            }
        }

    def build_timeline_comment_payload(
        self,
        lead_id: int,
        answers: dict[str, str],
        qualification: QualificationResult,
    ) -> dict[str, Any]:
        return {
            "fields": {
                "ENTITY_ID": lead_id,
                "ENTITY_TYPE": "lead",
                "COMMENT": build_case_snapshot(answers, qualification),
            }
        }

    @staticmethod
    def _extract_task_id(task_response: dict[str, Any]) -> int | None:
        if "task" in task_response and isinstance(task_response["task"], dict):
            task_id = task_response["task"].get("id")
            return int(task_id) if task_id else None
        if "item" in task_response and isinstance(task_response["item"], dict):
            task_id = task_response["item"].get("id")
            return int(task_id) if task_id else None
        return None

    @staticmethod
    def _build_status_description(
        answers: dict[str, str],
        qualification: QualificationResult,
    ) -> str:
        fit = {
            "target": "Целевой лид",
            "adjacent": "Смежное обращение",
            "non_target": "Нецелевое обращение",
        }.get(qualification.fit.value, "Целевой лид")
        route = {
            "bankruptcy": "банкротство",
            "family": "семейное право",
            "manual_review": "ручная проверка",
        }.get(qualification.route, "общий маршрут")
        return f"{fit}. Маршрут: {route}. Контакт: {answers.get('preferred_time', '-')}."


def _split_name(full_name: str) -> tuple[str, str]:
    parts = [part for part in full_name.split() if part]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _int_or_none(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
