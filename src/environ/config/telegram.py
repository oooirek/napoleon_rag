from pydantic_settings import BaseSettings, SettingsConfigDict

from src.environ.base import BASE_MODEL_CONFIG


class TelegramSettings(BaseSettings):
	BOT_TOKEN: str

	model_config = BASE_MODEL_CONFIG | SettingsConfigDict(env_prefix="TELEGRAM_")
