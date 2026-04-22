from __future__ import annotations

from dataclasses import dataclass

from app.config import Settings
from app.domain.models import LeadFit
from app.domain.questionnaire import PRACTICE_BANKRUPTCY, PRACTICE_DIVORCE, PRACTICE_PROPERTY


@dataclass(slots=True)
class RoutingDecision:
    fit: LeadFit
    route: str
    responsible_id: int
    bitrix_status_id: str
    reasons: list[str]


NON_TARGET_MARKERS = [
    "уголов",
    "арбитраж",
    "ооо",
    "юрлиц",
    "юр лицо",
    "юридическое лицо",
    "корпоратив",
    "налог",
    "тамож",
    "миграц",
    "договор постав",
    "госконтракт",
    "44-фз",
    "223-фз",
    "банкротство компании",
    "банкротство ооо",
]

ADJACENT_MARKERS = [
    "алим",
    "место жительства ребенка",
    "порядок общения",
    "наслед",
    "трудов",
    "увольнен",
    "зарплат",
    "недвижим",
    "дду",
    "застройщик",
    "потребител",
    "взыскан",
]

TARGET_MARKERS = {
    PRACTICE_BANKRUPTCY: ["долг", "кредит", "мфо", "банк", "пристав", "коллектор", "банкрот"],
    PRACTICE_DIVORCE: ["развод", "брак", "супруг", "супруга", "дет", "загс"],
    PRACTICE_PROPERTY: ["раздел", "кварт", "дом", "ипот", "авто", "счет", "имущество", "дол"],
}


def decide_route(answers: dict[str, str], settings: Settings) -> RoutingDecision:
    practice_area = answers.get("practice_area", "")
    combined_text = " ".join(
        str(answers.get(key, ""))
        for key in (
            "practice_area",
            "client_type",
            "situation_summary",
            "financial_or_family_context",
            "opposing_party",
            "region",
        )
    ).lower()
    reasons: list[str] = []

    route = _route_for_practice(practice_area)
    responsible_id = _responsible_for_route(route, settings)
    fit = LeadFit.TARGET
    status_id = settings.bitrix24_target_status_id

    if _has_any(combined_text, NON_TARGET_MARKERS):
        fit = LeadFit.NON_TARGET
        route = "manual_review"
        responsible_id = settings.bitrix24_review_responsible_id or settings.bitrix24_responsible_id
        status_id = settings.bitrix24_non_target_status_id
        reasons.append("В тексте есть маркеры нецелевого направления.")
    elif _has_any(combined_text, ADJACENT_MARKERS):
        fit = LeadFit.ADJACENT
        route = "manual_review"
        responsible_id = settings.bitrix24_review_responsible_id or settings.bitrix24_responsible_id
        status_id = settings.bitrix24_adjacent_status_id
        reasons.append("Запрос похож на смежную практику, нужна ручная проверка.")
    elif not _has_any(combined_text, TARGET_MARKERS.get(practice_area, [])):
        fit = LeadFit.ADJACENT
        status_id = settings.bitrix24_adjacent_status_id
        reasons.append("Выбрано целевое направление, но в тексте мало подтверждающих фактов.")
    else:
        reasons.append("Запрос соответствует текущей специализации.")

    return RoutingDecision(
        fit=fit,
        route=route,
        responsible_id=responsible_id,
        bitrix_status_id=status_id,
        reasons=reasons,
    )


def _route_for_practice(practice_area: str) -> str:
    if practice_area == PRACTICE_BANKRUPTCY:
        return "bankruptcy"
    if practice_area in {PRACTICE_DIVORCE, PRACTICE_PROPERTY}:
        return "family"
    return "manual_review"


def _responsible_for_route(route: str, settings: Settings) -> int:
    if route == "bankruptcy" and settings.bitrix24_bankruptcy_responsible_id:
        return settings.bitrix24_bankruptcy_responsible_id
    if route == "family" and settings.bitrix24_family_responsible_id:
        return settings.bitrix24_family_responsible_id
    if route == "manual_review" and settings.bitrix24_review_responsible_id:
        return settings.bitrix24_review_responsible_id
    return settings.bitrix24_responsible_id


def _has_any(text: str, markers: list[str]) -> bool:
    return any(marker in text for marker in markers)
