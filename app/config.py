from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    law_firm_name: str = Field(default="Prima Lex", alias="LAW_FIRM_NAME")
    manager_name: str = Field(default="Старший юрист", alias="MANAGER_NAME")

    bitrix24_webhook_url: str = Field(alias="BITRIX24_WEBHOOK_URL")
    bitrix24_entity_type_id: int = Field(default=1, alias="BITRIX24_ENTITY_TYPE_ID")
    bitrix24_responsible_id: int = Field(default=1, alias="BITRIX24_RESPONSIBLE_ID")
    bitrix24_creator_id: int | None = Field(default=None, alias="BITRIX24_CREATOR_ID")
    bitrix24_source_id: str = Field(default="WEB", alias="BITRIX24_SOURCE_ID")
    bitrix24_bankruptcy_responsible_id: int | None = Field(
        default=None,
        alias="BITRIX24_BANKRUPTCY_RESPONSIBLE_ID",
    )
    bitrix24_family_responsible_id: int | None = Field(
        default=None,
        alias="BITRIX24_FAMILY_RESPONSIBLE_ID",
    )
    bitrix24_review_responsible_id: int | None = Field(
        default=None,
        alias="BITRIX24_REVIEW_RESPONSIBLE_ID",
    )
    bitrix24_target_status_id: str = Field(default="IN_PROCESS", alias="BITRIX24_TARGET_STATUS_ID")
    bitrix24_adjacent_status_id: str = Field(default="NEW", alias="BITRIX24_ADJACENT_STATUS_ID")
    bitrix24_non_target_status_id: str = Field(default="JUNK", alias="BITRIX24_NON_TARGET_STATUS_ID")

    booking_url: str | None = Field(default=None, alias="BOOKING_URL")
    booking_slots: str = Field(
        default="Сегодня 16:00-18:00|Завтра 10:00-12:00|Завтра 15:00-17:00|Ближайший свободный слот",
        alias="BOOKING_SLOTS",
    )
    manager_telegram_chat_id: int | None = Field(default=None, alias="MANAGER_TELEGRAM_CHAT_ID")

    service_regions: list[str] = Field(
        default_factory=lambda: [
            "Москва",
            "Московская область",
            "Санкт-Петербург",
            "Ленинградская область",
            "Онлайн по РФ",
        ],
        alias="SERVICE_REGIONS",
    )

    reminder_after_minutes: int = Field(default=30, alias="REMINDER_AFTER_MINUTES")
    reminder_after_hours: int = Field(default=24, alias="REMINDER_AFTER_HOURS")
    qualified_follow_up_hours: int = Field(default=6, alias="QUALIFIED_FOLLOW_UP_HOURS")
    telegram_attachment_max_mb: int = Field(default=10, alias="TELEGRAM_ATTACHMENT_MAX_MB")

    llm_enabled: bool = Field(default=False, alias="LLM_ENABLED")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.2", alias="OPENAI_MODEL")
    openai_timeout_seconds: float = Field(default=20.0, alias="OPENAI_TIMEOUT_SECONDS")
    openai_max_output_tokens: int = Field(default=350, alias="OPENAI_MAX_OUTPUT_TOKENS")

    db_path: Path = Field(default=Path("data/legal_intake.sqlite3"), alias="DB_PATH")
    website_leads_jsonl_path: Path = Field(
        default=Path("site/data/site-leads.jsonl"),
        alias="WEBSITE_LEADS_JSONL_PATH",
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    @field_validator("service_regions", mode="before")
    @classmethod
    def parse_regions(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    @field_validator("booking_url", mode="before")
    @classmethod
    def empty_string_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @field_validator("openai_api_key", mode="before")
    @classmethod
    def empty_openai_key_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None

    @property
    def creator_id(self) -> int:
        return self.bitrix24_creator_id or self.bitrix24_responsible_id

    @property
    def booking_slot_options(self) -> list[str]:
        return [item.strip() for item in self.booking_slots.split("|") if item.strip()]

    def ensure_dirs(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
