import hashlib
import logging
from pathlib import Path

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.rag.ingest import DocumentIngestion
from src.rag.registry import SQLiteIngestRegistry
from src.tg_bot.runtime import container
from src.tg_bot.states import IngestState

log = logging.getLogger(__name__)

router = Router()

COLLECTION_NAME = "questions"
DOCS_DIR = Path(__file__).resolve().parents[3].joinpath("docs")
REGISTRY = SQLiteIngestRegistry()


def _file_sha256(file_path: Path) -> str:
	hasher = hashlib.sha256()
	with file_path.open("rb") as file:
		for chunk in iter(lambda: file.read(1024 * 1024), b""):
			hasher.update(chunk)
	return hasher.hexdigest()


@router.message(Command("ingest"))
async def ingest_start(message: Message, state: FSMContext) -> None:
	await state.set_state(IngestState.waiting_for_file)
	await message.answer("Отправь файл для индексации. В pdf формате. До 20 МБ.")


@router.message(IngestState.waiting_for_file)
async def ingest_file(message: Message, state: FSMContext, bot: Bot) -> None:
	if not message.document:
		await message.answer("Нужен файл. Пришли документ.")
		return

	file_name = message.document.file_name or "document"
	extension = Path(file_name).suffix.lower().lstrip(".")
	if not extension:
		await message.answer("Не удалось определить расширение файла.")
		return

	DOCS_DIR.mkdir(parents=True, exist_ok=True)
	target_path = DOCS_DIR.joinpath(f"{message.document.file_id}_{file_name}")

	file = await bot.get_file(message.document.file_id)
	await bot.download_file(file.file_path, destination=target_path)

	file_hash = _file_sha256(target_path)
	if REGISTRY.is_duplicate(file_hash):
		await message.answer("Документ уже был загружен. Индексация пропущена.")
		await state.clear()
		target_path.unlink(missing_ok=True)
		return

	status = await message.answer("Индексирую файл, подожди...")
	await state.clear()

	try:
		doc_ingestion = DocumentIngestion(container)

		if not await container.vector_store.is_collection_exists(collection_name=COLLECTION_NAME):
			await container.vector_store.create_collection(collection_name=COLLECTION_NAME)

		num_chunks = await doc_ingestion.ingest(
			file_path=str(target_path),
			collection_name=COLLECTION_NAME,
			file_extension=extension,
		)

		REGISTRY.add_record(
			file_hash=file_hash,
			file_name=file_name,
			file_size=message.document.file_size,
			source=str(target_path),
			num_chunks=num_chunks,
		)

		await status.edit_text(f"Файл проиндексирован. Чанков: {num_chunks}")
	except Exception:
		log.exception("Ingest failed for file %s", file_name)
		await status.edit_text("Ошибка индексации. Проверь файл и попробуй снова.")
	finally:
		target_path.unlink(missing_ok=True)
