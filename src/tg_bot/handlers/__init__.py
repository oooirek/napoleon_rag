from aiogram import Router

from src.tg_bot.handlers.cancel import router as cancel_router
from src.tg_bot.handlers.ingest import router as ingest_router
from src.tg_bot.handlers.query import router as query_router
from src.tg_bot.handlers.start import router as start_router

router = Router()
router.include_router(start_router)
router.include_router(ingest_router)
router.include_router(query_router)
router.include_router(cancel_router)
