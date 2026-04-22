from __future__ import annotations

from app.config import Settings
from app.domain.models import IntakeQuestion


PRACTICE_BANKRUPTCY = "Банкротство физического лица"
PRACTICE_DIVORCE = "Развод"
PRACTICE_PROPERTY = "Раздел имущества"
PRACTICE_OTHER = "Нужно уточнить направление"

CLIENT_TYPE_INDIVIDUAL = "Физическое лицо"

SUPPORTED_PRACTICE_AREAS = {
    PRACTICE_BANKRUPTCY,
    PRACTICE_DIVORCE,
    PRACTICE_PROPERTY,
}


def build_questions(settings: Settings) -> list[IntakeQuestion]:
    region_options = settings.service_regions[:]
    if "Другой регион" not in region_options:
        region_options.append("Другой регион")
    booking_slot_options = settings.booking_slot_options or ["Ближайший свободный слот"]

    return [
        IntakeQuestion(
            key="practice_area",
            prompt=(
                "С каким вопросом нужна помощь?\n"
                "Мы работаем с физическими лицами по трем направлениям."
            ),
            options=[
                PRACTICE_BANKRUPTCY,
                PRACTICE_DIVORCE,
                PRACTICE_PROPERTY,
                PRACTICE_OTHER,
            ],
        ),
        IntakeQuestion(
            key="client_type",
            prompt="Подтвердите, что обращение от физического лица.",
            options=[CLIENT_TYPE_INDIVIDUAL],
        ),
        IntakeQuestion(
            key="situation_summary",
            prompt=(
                "Кратко опишите ситуацию в 2-4 предложениях.\n"
                "Что произошло, какие документы есть и какого результата хотите добиться?"
            ),
            placeholder="Например: есть кредиты и исполнительные производства, нужна оценка банкротства.",
        ),
        IntakeQuestion(
            key="urgency",
            prompt="Насколько срочный вопрос?",
            options=["Сегодня", "В ближайшие 3 дня", "1-2 недели", "Пока просто консультация"],
        ),
        IntakeQuestion(
            key="deadline_details",
            prompt=(
                "Есть ли важная дата: суд, заседание, сделка, срок ответа, приставы или дата платежа?\n"
                "Если есть, напишите дату и что нужно успеть."
            ),
            placeholder="Если срочности нет, напишите: Нет срочного дедлайна.",
        ),
        IntakeQuestion(
            key="financial_or_family_context",
            prompt=(
                "Уточните ключевые факты по направлению:\n"
                "банкротство - сумма долга, банки/МФО, имущество;\n"
                "развод - есть ли дети и согласие супруга;\n"
                "раздел имущества - что нужно делить: квартира, авто, ипотека, счета."
            ),
        ),
        IntakeQuestion(
            key="opposing_party",
            prompt=(
                "Кто вторая сторона или ключевой участник ситуации?\n"
                "Например: супруг/супруга, банк, кредитор, пристав. Если не знаете, напишите: Не знаю."
            ),
        ),
        IntakeQuestion(
            key="documents_ready",
            prompt="Документы уже есть?",
            options=["Да, все основные", "Частично", "Пока нет"],
        ),
        IntakeQuestion(
            key="region",
            prompt="В каком регионе нужно вести вопрос?",
            options=region_options,
        ),
        IntakeQuestion(
            key="consultation_format",
            prompt="Как удобнее провести первую консультацию?",
            options=["Телефон", "Telegram", "Онлайн-встреча", "Личный визит"],
        ),
        IntakeQuestion(
            key="consultation_terms_ack",
            prompt=(
                "Первичная диагностика помогает понять маршрут. Стоимость и формат консультации "
                "согласуются после оценки ситуации. Подходит?"
            ),
            options=["Да, подходит", "Нужно сначала уточнить условия"],
        ),
        IntakeQuestion(
            key="full_name",
            prompt="Как к вам обращаться? Укажите имя и фамилию.",
        ),
        IntakeQuestion(
            key="phone",
            prompt="Оставьте номер телефона для связи.",
            placeholder="Например: +7 999 123-45-67",
        ),
        IntakeQuestion(
            key="email",
            prompt="Укажите e-mail, если удобно. Если нет, напишите: Нет.",
        ),
        IntakeQuestion(
            key="preferred_time",
            prompt=(
                "Выберите предварительное окно для первой консультации.\n"
                "Юрист подтвердит точное время после проверки заявки."
            ),
            options=booking_slot_options,
        ),
        IntakeQuestion(
            key="lead_source",
            prompt="Откуда вы узнали о нас?",
            options=["Сайт", "Google / поиск", "Рекомендация", "Соцсети", "Повторное обращение", "Другое"],
        ),
    ]
