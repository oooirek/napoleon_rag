from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
	await state.clear()
	await message.answer("Действие отменено.")
