from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
	text = (
		"Доступные команды:\n"
		"/ingest — загрузить документ для индексации\n"
		"/query_to_llm — задать вопрос по документам\n"
		"/cancel — отменить текущее действие"
	)
	await message.answer(text)
