from __future__ import annotations

import asyncio
from io import BytesIO
import re
from dataclasses import asdict
from datetime import timedelta
from typing import Any

from aiogram import Bot
from aiogram.types import User

from app.config import Settings
from app.domain.models import Prompt, ReminderType
from app.domain.qualification import evaluate_lead
from app.domain.questionnaire import build_questions
from app.integrations.bitrix24 import Bitrix24Client
from app.services.formatters import (
    build_manager_notification,
    build_post_submit_follow_up,
    build_reminder_text,
    build_user_confirmation,
)
from app.services.llm import LLMAssistant
from app.storage.sqlite import SQLiteStorage, utcnow
from app.services.website_leads import WebsiteLeadStore


PHONE_RE = re.compile(r"[\d\+\-\(\)\s]{10,25}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class IntakeCoordinator:
    def __init__(
        self,
        settings: Settings,
        storage: SQLiteStorage,
        bitrix_client: Bitrix24Client,
        bot: Bot,
    ) -> None:
        self.settings = settings
        self.storage = storage
        self.bitrix_client = bitrix_client
        self.bot = bot
        self.questions = build_questions(settings)
        self.website_leads = WebsiteLeadStore(settings.website_leads_jsonl_path)
        self.llm = LLMAssistant(settings)

    async def start(self, chat_id: int, user: User) -> Prompt:
        existing_session = self.storage.get_session(chat_id)
        if existing_session:
            question = self.questions[existing_session["step_index"]]
            return Prompt(
                text=(
                    "У нас уже открыт диалог по вашей заявке. Продолжим с текущего шага.\n\n"
                    f"{question.prompt}"
                ),
                options=question.options,
            )

        completed = self.storage.get_completed_chat(chat_id)
        if completed:
            return Prompt(
                text=(
                    "Ваша заявка уже передана юристу. "
                    "Если хотите создать новую заявку, отправьте /restart.\n\n"
                    "Если нужно дослать документ или уточнение, просто напишите его сюда."
                ),
                remove_keyboard=True,
            )

        session = self._new_session(user)
        self.storage.save_session(chat_id, session)
        self.storage.delete_completed_chat(chat_id)
        self.storage.cancel_pending_reminders(chat_id)
        self._schedule_incomplete_reminders(chat_id)
        first_question = self.questions[0]
        greeting = (
            f"Здравствуйте. Я помогу быстро передать запрос в {self.settings.law_firm_name} "
            "и собрать первичную информацию для юриста.\n\n"
            "Это займет 2-3 минуты."
        )
        return Prompt(
            text=f"{greeting}\n\n{first_question.prompt}",
            options=first_question.options,
        )

    async def restart(self, chat_id: int, user: User) -> Prompt:
        self.storage.delete_session(chat_id)
        self.storage.delete_completed_chat(chat_id)
        self.storage.cancel_pending_reminders(chat_id)
        return await self.start(chat_id, user)

    def llm_status(self) -> str:
        return self.llm.status_text()

    async def start_from_website(self, chat_id: int, user: User, request_id: str) -> Prompt:
        completed = self.storage.get_completed_chat(chat_id)
        if completed and completed.get("answers", {}).get("website_request_id") == request_id:
            return Prompt(
                text=(
                    "Эта заявка уже передана юристу. "
                    "Если хотите дослать документ или уточнение, просто напишите его сюда."
                ),
                remove_keyboard=True,
            )

        event = self.website_leads.find_by_request_id(request_id)
        if not event:
            return Prompt(
                text=(
                    "Я не нашел заявку с сайта по этой ссылке. "
                    "Можно начать заново: нажмите /start или отправьте новую заявку на сайте."
                ),
                remove_keyboard=True,
            )

        lead = event.get("lead", {})
        crm = event.get("crm", {})
        answers = self._new_session(user)["answers"]
        answers.update(self._website_lead_to_answers(lead, crm))

        self.storage.delete_session(chat_id)
        self.storage.save_completed_chat(
            chat_id,
            {
                "answers": answers,
                "lead_id": _int_or_none(crm.get("leadId")),
                "task_id": _int_or_none(crm.get("taskId")),
                "status": "website_submitted",
            },
        )
        self.storage.cancel_pending_reminders(chat_id)

        return Prompt(
            text=(
                "Вижу вашу заявку с сайта. Она уже передана юристу, повторно заполнять ничего не нужно.\n\n"
                "Этот чат можно использовать, чтобы дослать документы, фото, уточнения или задать вопрос "
                "по уже созданной заявке. Всё, что вы напишете здесь, будет добавлено в карточку лида."
            ),
            remove_keyboard=True,
        )

    async def handle_text(self, chat_id: int, text: str, user: User) -> Prompt:
        session = self.storage.get_session(chat_id)
        if not session:
            completed = self.storage.get_completed_chat(chat_id)
            if completed:
                return await self._handle_completed_followup(chat_id, text, completed)
            return await self.start(chat_id, user)

        question = self.questions[session["step_index"]]
        normalized_answer, error = self._validate_answer(question.key, text, question.options)
        if error:
            return Prompt(text=error, options=question.options)

        session["answers"][question.key] = normalized_answer
        session["step_index"] = self._next_missing_step(session["step_index"] + 1, session["answers"])
        session["updated_at"] = utcnow().isoformat()
        self.storage.save_session(chat_id, session)
        self.storage.cancel_pending_reminders(chat_id, ReminderType.INCOMPLETE.value)

        if session["step_index"] < len(self.questions):
            self._schedule_incomplete_reminders(chat_id)
            next_question = self.questions[session["step_index"]]
            return Prompt(text=next_question.prompt, options=next_question.options)

        return await self._finalize_session(chat_id, session)

    async def handle_attachment(
        self,
        chat_id: int,
        user: User,
        file_id: str,
        file_name: str,
        file_size: int | None,
        caption: str | None = None,
    ) -> Prompt:
        session = self.storage.get_session(chat_id)
        if session:
            return Prompt(
                text=(
                    "Файл вижу, но сначала нужно завершить текущую заявку. "
                    "Ответьте на последний вопрос, а после передачи лида юристу можно будет дослать документы сюда."
                ),
                remove_keyboard=True,
            )

        completed = self.storage.get_completed_chat(chat_id)
        if not completed:
            return Prompt(
                text=(
                    "Чтобы прикрепить файл к делу, сначала создайте заявку на сайте или через /start. "
                    "После этого документы можно будет отправлять прямо сюда."
                ),
                remove_keyboard=True,
            )

        max_bytes = self.settings.telegram_attachment_max_mb * 1024 * 1024
        if file_size and file_size > max_bytes:
            return Prompt(
                text=(
                    f"Файл слишком большой. Сейчас лимит для Telegram-вложений: "
                    f"{self.settings.telegram_attachment_max_mb} МБ."
                ),
                remove_keyboard=True,
            )

        lead_id = self._resolve_completed_lead_id(chat_id, completed)
        if not lead_id:
            return Prompt(
                text=(
                    "Файл получил, но пока не смог найти связанную карточку Bitrix. "
                    "Попробуйте позже или дождитесь связи юриста."
                ),
                remove_keyboard=True,
            )

        try:
            content = await self._download_telegram_file(file_id)
            await self.bitrix_client.add_timeline_comment(
                lead_id,
                self._build_attachment_comment(file_name, caption, user),
                files=[(file_name, content)],
            )
        except Exception:
            return Prompt(
                text=(
                    "Не смог прикрепить файл к карточке Bitrix. "
                    "Попробуйте отправить его еще раз чуть позже."
                ),
                remove_keyboard=True,
            )

        return Prompt(
            text="Спасибо, файл прикрепил к карточке лида. Юрист увидит его вместе с заявкой.",
            remove_keyboard=True,
        )

    async def _finalize_session(self, chat_id: int, session: dict[str, Any]) -> Prompt:
        answers = session["answers"]
        qualification = evaluate_lead(answers, self.settings)
        bitrix_result = await self.bitrix_client.submit_intake(chat_id, answers, qualification)
        self.storage.save_submission(
            chat_id=chat_id,
            status=qualification.status.value,
            score=qualification.score,
            payload={"answers": answers, "qualification": asdict(qualification)},
            lead_id=bitrix_result.lead_id,
            task_id=bitrix_result.task_id,
        )
        self.storage.save_completed_chat(
            chat_id,
            {
                "answers": answers,
                "lead_id": bitrix_result.lead_id,
                "task_id": bitrix_result.task_id,
                "status": qualification.status.value,
            },
        )
        self.storage.delete_session(chat_id)
        self.storage.cancel_pending_reminders(chat_id)

        if qualification.status.value in {"hot", "qualified", "review"}:
            self._schedule_qualified_follow_up(chat_id)

        await self._notify_manager(answers, qualification, bitrix_result)
        return Prompt(
            text=build_user_confirmation(answers, qualification, bitrix_result, self.settings),
            remove_keyboard=True,
        )

    async def _add_followup_to_completed_lead(
        self,
        chat_id: int,
        text: str,
        completed: dict[str, Any],
    ) -> bool:
        lead_id = self._resolve_completed_lead_id(chat_id, completed)
        if not lead_id:
            return False
        try:
            await self.bitrix_client.add_timeline_comment(
                int(lead_id),
                f"Уточнение из Telegram после завершения заявки:\n{text}",
            )
            return True
        except Exception:
            return False

    async def _handle_completed_followup(
        self,
        chat_id: int,
        text: str,
        completed: dict[str, Any],
    ) -> Prompt:
        added = await self._add_followup_to_completed_lead(chat_id, text, completed)
        if not added:
            return Prompt(
                text=(
                    "Я сохранил ваше сообщение в чате, но сейчас не смог добавить его в карточку Bitrix. "
                    "Пожалуйста, попробуйте еще раз чуть позже или дождитесь связи юриста."
                ),
                remove_keyboard=True,
            )

        ai_reply = await self.llm.answer_followup(text, completed.get("answers", {}))
        if not ai_reply:
            return Prompt(
                text=(
                    "Спасибо, добавил уточнение к вашей заявке. "
                    "Юрист увидит его в карточке лида."
                ),
                remove_keyboard=True,
            )

        lead_id = self._resolve_completed_lead_id(chat_id, completed)
        if lead_id:
            try:
                await self.bitrix_client.add_timeline_comment(
                    int(lead_id),
                    "AI-ответ клиенту в Telegram после завершения заявки:\n" + ai_reply,
                )
            except Exception:
                pass

        return Prompt(
            text=(
                "Спасибо, добавил уточнение к вашей заявке. Юрист увидит его в карточке лида.\n\n"
                "Предварительный AI-ответ, не заменяет консультацию юриста:\n"
                f"{ai_reply}"
            ),
            remove_keyboard=True,
        )

    def _resolve_completed_lead_id(self, chat_id: int, completed: dict[str, Any]) -> int | None:
        lead_id = _int_or_none(completed.get("lead_id"))
        if lead_id:
            return lead_id

        request_id = completed.get("answers", {}).get("website_request_id")
        if not request_id:
            return None

        event = self.website_leads.find_by_request_id(request_id)
        crm = event.get("crm", {}) if event else {}
        lead_id = _int_or_none(crm.get("leadId"))
        if not lead_id:
            return None

        refreshed = {
            **completed,
            "lead_id": lead_id,
            "task_id": _int_or_none(crm.get("taskId")) or completed.get("task_id"),
        }
        self.storage.save_completed_chat(chat_id, refreshed)
        return lead_id

    async def _download_telegram_file(self, file_id: str) -> bytes:
        telegram_file = await self.bot.get_file(file_id)
        buffer = BytesIO()
        await self.bot.download_file(telegram_file.file_path, destination=buffer)
        return buffer.getvalue()

    def _build_attachment_comment(self, file_name: str, caption: str | None, user: User) -> str:
        lines = [
            "Документ из Telegram после завершения заявки:",
            f"Файл: {file_name}",
            f"Отправитель: {user.full_name}",
        ]
        if user.username:
            lines.append(f"Telegram: @{user.username}")
        if caption:
            lines.extend(["", "Комментарий клиента:", caption])
        return "\n".join(lines)

    async def run_reminder_loop(self) -> None:
        while True:
            due = self.storage.list_due_reminders(utcnow())
            for reminder in due:
                await self._process_reminder(reminder)
                self.storage.mark_reminder_sent(reminder.reminder_id)
            await asyncio.sleep(30)

    async def _process_reminder(self, reminder: Any) -> None:
        if reminder.reminder_type == ReminderType.INCOMPLETE.value:
            if self.storage.get_completed_chat(reminder.chat_id):
                self.storage.cancel_pending_reminders(reminder.chat_id, ReminderType.INCOMPLETE.value)
                return

            session = self.storage.get_session(reminder.chat_id)
            if not session:
                return
            if session.get("answers", {}).get("website_request_id"):
                self.storage.delete_session(reminder.chat_id)
                self.storage.cancel_pending_reminders(reminder.chat_id, ReminderType.INCOMPLETE.value)
                return
            question = self.questions[session["step_index"]]
            await self.bot.send_message(
                reminder.chat_id,
                build_reminder_text(question.prompt, self.settings),
            )
            return

        if reminder.reminder_type == ReminderType.QUALIFIED.value:
            await self.bot.send_message(
                reminder.chat_id,
                build_post_submit_follow_up(self.settings),
            )

    async def _notify_manager(self, answers: dict[str, str], qualification, bitrix_result) -> None:
        if not self.settings.manager_telegram_chat_id:
            return
        try:
            await self.bot.send_message(
                self.settings.manager_telegram_chat_id,
                build_manager_notification(answers, qualification, bitrix_result, self.settings),
            )
        except Exception:
            return

    def _new_session(self, user: User) -> dict[str, Any]:
        return {
            "step_index": 0,
            "answers": {
                "telegram_user_id": str(user.id),
                "telegram_username": user.username or "",
                "telegram_display_name": user.full_name,
            },
            "updated_at": utcnow().isoformat(),
        }

    def _website_lead_to_answers(self, lead: dict[str, Any], crm: dict[str, Any]) -> dict[str, str]:
        return {
            "website_request_id": str(lead.get("requestId", "")),
            "website_bitrix_lead_id": str(crm.get("leadId") or ""),
            "practice_area": self._map_service_to_practice(str(lead.get("service", ""))),
            "client_type": self.questions[1].options[0],
            "situation_summary": str(lead.get("situation", "")),
            "urgency": self._map_urgency(str(lead.get("urgency", ""))),
            "consultation_format": self._map_contact_format(str(lead.get("contact", ""))),
            "full_name": str(lead.get("name", "")),
            "phone": str(lead.get("phone", "")),
            "lead_source": self.questions[15].options[0],
        }

    def _next_missing_step(self, start_index: int, answers: dict[str, str]) -> int:
        for index in range(start_index, len(self.questions)):
            question = self.questions[index]
            if not answers.get(question.key):
                return index
        return len(self.questions)

    def _map_service_to_practice(self, service_slug: str) -> str:
        practice_options = self.questions[0].options
        if service_slug == "bankrotstvo-fizicheskih-lic":
            return practice_options[0]
        if service_slug == "razvod":
            return practice_options[1]
        if service_slug == "razdel-imushchestva":
            return practice_options[2]
        return practice_options[-1]

    def _map_urgency(self, urgency: str) -> str:
        urgency_options = self.questions[3].options
        urgency_lower = urgency.lower()
        if "3" in urgency:
            return urgency_options[1]
        if "1-2" in urgency:
            return urgency_options[2]
        if "сегодня" in urgency_lower or "today" in urgency_lower:
            return urgency_options[0]
        return urgency_options[-1]

    def _map_contact_format(self, contact: str) -> str:
        options = self.questions[9].options
        lowered = contact.lower()
        if "telegram" in lowered:
            return next((option for option in options if "telegram" in option.lower()), options[0])
        if "онлайн" in lowered:
            return next((option for option in options if "онлайн" in option.lower()), options[0])
        if options:
            return options[0]
        return contact

    def _schedule_incomplete_reminders(self, chat_id: int) -> None:
        now = utcnow()
        self.storage.schedule_reminder(
            chat_id,
            ReminderType.INCOMPLETE.value,
            now + timedelta(minutes=self.settings.reminder_after_minutes),
            {},
        )
        self.storage.schedule_reminder(
            chat_id,
            ReminderType.INCOMPLETE.value,
            now + timedelta(hours=self.settings.reminder_after_hours),
            {},
        )

    def _schedule_qualified_follow_up(self, chat_id: int) -> None:
        due_at = utcnow() + timedelta(hours=self.settings.qualified_follow_up_hours)
        self.storage.schedule_reminder(chat_id, ReminderType.QUALIFIED.value, due_at, {})

    def _validate_answer(
        self,
        key: str,
        value: str,
        options: list[str],
    ) -> tuple[str, str | None]:
        cleaned = value.strip()
        if not cleaned:
            return "", "Нужен ответ, чтобы я смог продолжить заявку."

        if options:
            normalized = _normalize_choice(cleaned, options)
            if normalized is None:
                return "", "Пожалуйста, выберите один из вариантов на клавиатуре."
            return normalized, None

        if key == "situation_summary" and len(cleaned) < 20:
            return "", "Нужно чуть больше деталей: хотя бы 20 символов о сути ситуации."
        if key == "full_name" and len(cleaned) < 5:
            return "", "Укажите имя и фамилию, чтобы юрист корректно обратился к вам."
        if key == "phone" and not PHONE_RE.match(cleaned):
            return "", "Похоже, номер неполный. Укажите телефон в формате вроде +7 999 123-45-67."
        if key == "email" and cleaned.lower() != "нет" and not EMAIL_RE.match(cleaned):
            return "", "Если хотите оставить e-mail, укажите адрес в обычном формате или напишите: Нет."
        if key in {"deadline_details", "opposing_party", "preferred_time"} and len(cleaned) < 3:
            return "", "Нужен чуть более полный ответ, хотя бы несколько слов."

        return cleaned, None


def _normalize_choice(value: str, options: list[str]) -> str | None:
    lowered = value.lower()
    for option in options:
        if option.lower() == lowered:
            return option
    return None


def _int_or_none(value: object) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
