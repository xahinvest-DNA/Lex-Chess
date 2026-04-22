from __future__ import annotations

import asyncio
import contextlib
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.handlers import build_router
from app.config import get_settings
from app.integrations.bitrix24 import Bitrix24Client
from app.services.intake import IntakeCoordinator
from app.storage.sqlite import SQLiteStorage


async def amain() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    storage = SQLiteStorage(settings.db_path)
    storage.init()
    cleared = storage.clear_website_handoff_sessions()
    if cleared:
        logging.info("Cleared %s stale website handoff sessions", cleared)

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    bitrix_client = Bitrix24Client(settings)
    coordinator = IntakeCoordinator(settings, storage, bitrix_client, bot)

    dispatcher = Dispatcher()
    dispatcher.include_router(build_router(coordinator))

    reminder_task = asyncio.create_task(coordinator.run_reminder_loop())
    try:
        await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())
    finally:
        reminder_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await reminder_task
        await bitrix_client.close()
        await bot.session.close()


def run() -> None:
    asyncio.run(amain())


if __name__ == "__main__":
    run()
