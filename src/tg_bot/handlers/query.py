from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.rag.query import query_rag
from src.tg_bot.runtime import container
from src.tg_bot.states import QueryState

router = Router()

COLLECTION_NAME = "questions"


@router.message(Command("query_to_llm"))
async def query_start(message: Message, state: FSMContext) -> None:
	await state.set_state(QueryState.waiting_for_query)
	await message.answer("Отправь текстовый запрос.")


@router.message(QueryState.waiting_for_query)
async def query_text(message: Message, state: FSMContext) -> None:
	if not message.text:
		await message.answer("Нужен текстовый запрос.")
		return

	if not await container.vector_store.is_collection_exists(collection_name=COLLECTION_NAME):
		await message.answer("Коллекция не найдена. Сначала загрузите документы через /ingest.")
		await state.clear()
		return

	response = await query_rag(
		container=container,
		query=message.text,
		collection_name=COLLECTION_NAME,
	)

	await state.clear()
	await message.answer(response)
