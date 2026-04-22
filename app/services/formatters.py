from __future__ import annotations

from datetime import datetime
from html import escape

from app.config import Settings
from app.domain.models import BitrixSubmissionResult, LeadStatus, QualificationResult


def build_case_snapshot(answers: dict[str, str], qualification: QualificationResult) -> str:
    return (
        f"Практика: {answers.get('practice_area', '-')}\n"
        f"Клиент: {answers.get('full_name', '-')}\n"
        f"Телефон: {answers.get('phone', '-')}\n"
        f"E-mail: {answers.get('email', '-')}\n"
        f"Предпочтительное время: {answers.get('preferred_time', '-')}\n"
        f"Формат консультации: {answers.get('consultation_format', '-')}\n"
        f"Регион: {answers.get('region', '-')}\n"
        f"Срочность: {answers.get('urgency', '-')}\n"
        f"Дедлайн: {answers.get('deadline_details', '-')}\n"
        f"Вторая сторона: {answers.get('opposing_party', '-')}\n"
        f"Документы: {answers.get('documents_ready', '-')}\n"
        f"Маршрут: {_human_fit(qualification.fit.value)}. {_human_route(qualification.route)}.\n"
        f"\nСитуация:\n{answers.get('situation_summary', '-')}"
    )


def build_manager_notification(
    answers: dict[str, str],
    qualification: QualificationResult,
    bitrix_result: BitrixSubmissionResult,
    settings: Settings,
) -> str:
    lines = [
        f"<b>Новый лид: {escape(answers.get('practice_area', 'Без категории'))}</b>",
        f"Статус: <b>{escape(_status_label(qualification.status))}</b>",
        f"Fit: <b>{escape(qualification.fit.value)}</b>",
        f"Маршрут: <b>{escape(qualification.route)}</b>",
        f"Скоринг: <b>{qualification.score}</b>",
        f"Клиент: {escape(answers.get('full_name', '-'))}",
        f"Телефон: {escape(answers.get('phone', '-'))}",
        f"Регион: {escape(answers.get('region', '-'))}",
        f"Срочность: {escape(answers.get('urgency', '-'))}",
        f"Удобное время: {escape(answers.get('preferred_time', '-'))}",
        f"Кратко: {escape(answers.get('situation_summary', '-'))}",
    ]
    if bitrix_result.lead_id:
        lines.append(f"Bitrix lead ID: <b>{bitrix_result.lead_id}</b>")
    if bitrix_result.task_id:
        lines.append(f"Bitrix task ID: <b>{bitrix_result.task_id}</b>")
    if bitrix_result.error_message:
        lines.append(f"Ошибка CRM: <b>{escape(bitrix_result.error_message)}</b>")
    lines.append(f"Ответственный: {escape(settings.manager_name)}")
    return "\n".join(lines)


def build_user_confirmation(
    answers: dict[str, str],
    qualification: QualificationResult,
    bitrix_result: BitrixSubmissionResult,
    settings: Settings,
) -> str:
    status_text = {
        LeadStatus.HOT: "Ситуацию пометил как срочную.",
        LeadStatus.QUALIFIED: "Заявку передал юристу на быстрый разбор.",
        LeadStatus.REVIEW: "Заявку передал на ручной разбор юристом.",
        LeadStatus.LOW_FIT: "Заявку сохранил и передал на дополнительную проверку.",
    }[qualification.status]

    lines = [
        "Спасибо, заявку зафиксировал.",
        status_text,
        f"Предварительное окно консультации: {escape(answers.get('preferred_time', '-'))}.",
        f"{escape(settings.manager_name)} свяжется с вами в ориентире до {qualification.recommended_response_hours} ч.",
    ]

    if settings.booking_url:
        lines.append(
            f"Если хотите ускорить процесс, можно сразу выбрать слот: {escape(settings.booking_url)}"
        )

    if bitrix_result.error_message:
        lines.append(
            "CRM сейчас отвечает с ошибкой, но заявка не потеряна: я сохранил ее локально и отправил сигнал менеджеру."
        )

    return "\n\n".join(lines)


def build_reminder_text(
    question_prompt: str,
    settings: Settings,
) -> str:
    return (
        "Возвращаю вас к заявке. Мы сохранили ответы, и можно продолжить без повтора.\n\n"
        f"Следующий шаг:\n{question_prompt}\n\n"
        f"Если удобнее, просто напишите /restart и начнем заново для {settings.law_firm_name}."
    )


def build_post_submit_follow_up(settings: Settings) -> str:
    if settings.booking_url:
        return (
            "Если вопрос еще актуален, можно сразу выбрать удобное время консультации:\n"
            f"{escape(settings.booking_url)}\n\n"
            "Если удобнее, просто ответьте сообщением, и юрист свяжется с вами вручную."
        )
    return (
        "Проверяю, актуален ли еще ваш запрос. Если нужна консультация, просто ответьте в этот чат, "
        "и мы приоритезируем обратную связь."
    )


def bitrix_task_deadline(hours: int) -> str:
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def _status_label(status: LeadStatus) -> str:
    return {
        LeadStatus.HOT: "Срочный",
        LeadStatus.QUALIFIED: "Квалифицирован",
        LeadStatus.REVIEW: "Нужен разбор",
        LeadStatus.LOW_FIT: "Низкий fit",
    }[status]


def _human_fit(fit: str) -> str:
    return {
        "target": "целевой лид",
        "adjacent": "смежное обращение",
        "non_target": "нецелевое обращение",
    }.get(fit, "целевой лид")


def _human_route(route: str) -> str:
    return {
        "bankruptcy": "банкротство",
        "family": "семейное право",
        "manual_review": "ручная проверка",
    }.get(route, "общий маршрут")
