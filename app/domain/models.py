from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class LeadStatus(str, Enum):
    HOT = "hot"
    QUALIFIED = "qualified"
    REVIEW = "review"
    LOW_FIT = "low_fit"


class LeadFit(str, Enum):
    TARGET = "target"
    ADJACENT = "adjacent"
    NON_TARGET = "non_target"


class ReminderType(str, Enum):
    INCOMPLETE = "incomplete"
    QUALIFIED = "qualified"


@dataclass(slots=True)
class IntakeQuestion:
    key: str
    prompt: str
    options: list[str] = field(default_factory=list)
    placeholder: str | None = None


@dataclass(slots=True)
class Prompt:
    text: str
    options: list[str] = field(default_factory=list)
    remove_keyboard: bool = False


@dataclass(slots=True)
class QualificationResult:
    status: LeadStatus
    score: int
    manager_priority: str
    recommended_response_hours: int
    tags: list[str]
    rationale: list[str]
    fit: LeadFit = LeadFit.TARGET
    route: str = "general"
    responsible_id: int | None = None
    bitrix_status_id: str | None = None


@dataclass(slots=True)
class BitrixSubmissionResult:
    lead_id: int | None = None
    task_id: int | None = None
    timeline_comment_id: int | None = None
    error_message: str | None = None
