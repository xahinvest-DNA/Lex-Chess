from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove


def reply_keyboard(options: list[str]) -> ReplyKeyboardMarkup | None:
    if not options:
        return None

    rows = []
    row: list[KeyboardButton] = []
    for option in options:
        row.append(KeyboardButton(text=option))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)

    return ReplyKeyboardMarkup(
        keyboard=rows,
        resize_keyboard=True,
        one_time_keyboard=False,
        input_field_placeholder="Выберите вариант или введите ответ",
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove(remove_keyboard=True)
