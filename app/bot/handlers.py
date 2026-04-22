from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from app.bot.keyboards import remove_keyboard, reply_keyboard
from app.services.intake import IntakeCoordinator


def build_router(coordinator: IntakeCoordinator) -> Router:
    router = Router()

    @router.message(CommandStart())
    async def on_start(message: Message, command: CommandObject) -> None:
        start_payload = command.args if command else None
        if start_payload and start_payload.startswith("lead_"):
            prompt = await coordinator.start_from_website(
                message.chat.id,
                message.from_user,
                start_payload.removeprefix("lead_"),
            )
        else:
            prompt = await coordinator.start(message.chat.id, message.from_user)
        await message.answer(prompt.text, reply_markup=_markup(prompt))

    @router.message(Command("restart"))
    async def on_restart(message: Message) -> None:
        prompt = await coordinator.restart(message.chat.id, message.from_user)
        await message.answer(prompt.text, reply_markup=_markup(prompt))

    @router.message(Command("help"))
    async def on_help(message: Message) -> None:
        await message.answer(
            "Команды:\n"
            "/start - начать заявку\n"
            "/restart - начать заново\n"
            "/llm_status - проверить подключение AI\n"
            "/help - показать подсказку"
        )

    @router.message(Command("llm_status"))
    async def on_llm_status(message: Message) -> None:
        await message.answer(coordinator.llm_status())

    @router.message(F.text)
    async def on_text(message: Message) -> None:
        prompt = await coordinator.handle_text(message.chat.id, message.text, message.from_user)
        await message.answer(prompt.text, reply_markup=_markup(prompt))

    @router.message(F.photo | F.document)
    async def on_attachment(message: Message) -> None:
        attachment = _extract_attachment(message)
        if attachment is None:
            await message.answer("Не смог прочитать файл. Попробуйте отправить его еще раз.")
            return

        prompt = await coordinator.handle_attachment(
            chat_id=message.chat.id,
            user=message.from_user,
            file_id=attachment["file_id"],
            file_name=attachment["file_name"],
            file_size=attachment["file_size"],
            caption=message.caption,
        )
        await message.answer(prompt.text, reply_markup=_markup(prompt))

    @router.message()
    async def on_other(message: Message) -> None:
        await message.answer(
            "Я принимаю текст, фото и документы. Для новой заявки используйте /start."
        )

    return router


def _markup(prompt):
    if prompt.remove_keyboard or not prompt.options:
        return remove_keyboard()
    return reply_keyboard(prompt.options)


def _extract_attachment(message: Message) -> dict[str, object] | None:
    if message.document:
        document = message.document
        return {
            "file_id": document.file_id,
            "file_name": document.file_name or f"telegram_document_{document.file_unique_id}",
            "file_size": document.file_size,
        }

    if message.photo:
        photo = message.photo[-1]
        suffix = message.date.strftime("%Y%m%d_%H%M%S") if message.date else photo.file_unique_id
        return {
            "file_id": photo.file_id,
            "file_name": f"telegram_photo_{suffix}.jpg",
            "file_size": photo.file_size,
        }

    return None
