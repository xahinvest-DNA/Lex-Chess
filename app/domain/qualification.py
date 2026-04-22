from __future__ import annotations

from app.config import Settings
from app.domain.models import LeadFit, LeadStatus, QualificationResult
from app.domain.questionnaire import (
    CLIENT_TYPE_INDIVIDUAL,
    PRACTICE_BANKRUPTCY,
    PRACTICE_DIVORCE,
    PRACTICE_PROPERTY,
    SUPPORTED_PRACTICE_AREAS,
)
from app.domain.routing import decide_route


def evaluate_lead(answers: dict[str, str], settings: Settings) -> QualificationResult:
    score = 0
    tags: list[str] = []
    rationale: list[str] = []

    practice_area = answers.get("practice_area", "")
    client_type = answers.get("client_type", "")
    urgency = answers.get("urgency", "")
    region = answers.get("region", "")
    documents_ready = answers.get("documents_ready", "")
    terms_ack = answers.get("consultation_terms_ack", "")
    context = answers.get("financial_or_family_context", "")
    deadline_details = answers.get("deadline_details", "")
    consultation_format = answers.get("consultation_format", "")
    routing = decide_route(answers, settings)

    tags.extend([f"fit-{routing.fit.value}", f"route-{routing.route}"])
    rationale.extend(routing.reasons)

    if client_type == CLIENT_TYPE_INDIVIDUAL:
        score += 20
        tags.append("individual-client")
        rationale.append("Обращение от физического лица.")
    else:
        score -= 30
        tags.append("non-individual-risk")
        rationale.append("Сайт и бот сфокусированы только на физических лицах.")

    if practice_area in SUPPORTED_PRACTICE_AREAS:
        score += 30
        tags.append("practice-fit")
        rationale.append("Запрос относится к основной специализации.")
    else:
        score -= 20
        tags.append("manual-routing")
        rationale.append("Направление требует ручной проверки.")

    if practice_area == PRACTICE_BANKRUPTCY and _has_any(context, ["долг", "кредит", "мфо", "банк", "пристав"]):
        score += 12
        tags.append("bankruptcy-context")
        rationale.append("Есть факты, важные для диагностики банкротства.")
    if practice_area == PRACTICE_DIVORCE and _has_any(context, ["дет", "супруг", "супруга", "брак", "алим"]):
        score += 10
        tags.append("divorce-context")
        rationale.append("Есть семейно-правовой контекст.")
    if practice_area == PRACTICE_PROPERTY and _has_any(context, ["кварт", "дом", "ипот", "авто", "счет", "дол"]):
        score += 12
        tags.append("property-context")
        rationale.append("Указаны активы или долги для раздела.")

    urgency_scores = {
        "Сегодня": 22,
        "В ближайшие 3 дня": 16,
        "1-2 недели": 8,
        "Пока просто консультация": 3,
    }
    score += urgency_scores.get(urgency, 0)
    if urgency in {"Сегодня", "В ближайшие 3 дня"}:
        tags.append("urgent")
        rationale.append("Есть срочность, нужен быстрый контакт.")

    if deadline_details and "нет срочного дедлайна" not in deadline_details.lower():
        score += 10
        tags.append("has-deadline")
        rationale.append("Указана важная дата или процессуальный срок.")

    if _region_is_supported(region, settings):
        score += 8
        tags.append("region-fit")
        rationale.append("Регион соответствует зоне обслуживания.")
    elif "онлайн" in region.lower() or "рф" in region.lower():
        score += 6
        tags.append("online-fit")
    else:
        score -= 6
        rationale.append("Регион нужно проверить вручную.")

    if documents_ready == "Да, все основные":
        score += 9
        tags.append("documents-ready")
    elif documents_ready == "Частично":
        score += 4
    else:
        score -= 2

    if terms_ack == "Да, подходит":
        score += 8
        tags.append("terms-accepted")
    else:
        score += 1
        tags.append("terms-question")

    if consultation_format in {"Телефон", "Онлайн-встреча", "Личный визит"}:
        score += 5
    elif consultation_format == "Telegram":
        score += 3

    if routing.fit is LeadFit.ADJACENT:
        score -= 12
    elif routing.fit is LeadFit.NON_TARGET:
        score -= 45

    if routing.fit is LeadFit.NON_TARGET:
        return QualificationResult(
            status=LeadStatus.LOW_FIT,
            score=score,
            manager_priority="low",
            recommended_response_hours=48,
            tags=tags,
            rationale=rationale,
            fit=routing.fit,
            route=routing.route,
            responsible_id=routing.responsible_id,
            bitrix_status_id=routing.bitrix_status_id,
        )

    if score >= 72 or (
        routing.fit is LeadFit.TARGET
        and "urgent" in tags
        and "practice-fit" in tags
        and "individual-client" in tags
    ):
        return QualificationResult(
            status=LeadStatus.HOT,
            score=score,
            manager_priority="high",
            recommended_response_hours=1,
            tags=tags,
            rationale=rationale,
            fit=routing.fit,
            route=routing.route,
            responsible_id=routing.responsible_id,
            bitrix_status_id=routing.bitrix_status_id,
        )
    if score >= 52:
        return QualificationResult(
            status=LeadStatus.QUALIFIED,
            score=score,
            manager_priority="normal",
            recommended_response_hours=4,
            tags=tags,
            rationale=rationale,
            fit=routing.fit,
            route=routing.route,
            responsible_id=routing.responsible_id,
            bitrix_status_id=routing.bitrix_status_id,
        )
    if score >= 30:
        return QualificationResult(
            status=LeadStatus.REVIEW,
            score=score,
            manager_priority="review",
            recommended_response_hours=24,
            tags=tags,
            rationale=rationale,
            fit=routing.fit,
            route=routing.route,
            responsible_id=routing.responsible_id,
            bitrix_status_id=routing.bitrix_status_id,
        )
    return QualificationResult(
        status=LeadStatus.LOW_FIT,
        score=score,
        manager_priority="low",
        recommended_response_hours=48,
        tags=tags,
        rationale=rationale,
        fit=routing.fit,
        route=routing.route,
        responsible_id=routing.responsible_id,
        bitrix_status_id=routing.bitrix_status_id,
    )


def _region_is_supported(region: str, settings: Settings) -> bool:
    region_normalized = region.lower()
    return any(item.lower() in region_normalized for item in settings.service_regions)


def _has_any(text: str, markers: list[str]) -> bool:
    normalized = text.lower()
    return any(marker in normalized for marker in markers)
