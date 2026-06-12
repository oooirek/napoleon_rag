import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.environ.settings import settings
from src.logging_config import setup_logging
from src.tg_bot.handlers import router

log = logging.getLogger(__name__)


async def start_bot() -> None:
	setup_logging()
	log.info("Starting bot...")

	bot = Bot(
		token=settings.TELEGRAM.BOT_TOKEN,
		default=DefaultBotProperties(parse_mode=ParseMode.HTML),
	)
	dp = Dispatcher()
	dp.include_router(router)

	bot_info = await bot.get_me()
	log.info("Polling as @%s (id=%s)", bot_info.username, bot_info.id)

	await dp.start_polling(bot)


def run() -> None:
	asyncio.run(start_bot())
