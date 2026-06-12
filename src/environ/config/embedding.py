from pydantic_settings import BaseSettings, SettingsConfigDict

from src.environ.base import BASE_MODEL_CONFIG


class Embedding(BaseSettings):
	HOST: str
	PORT: int
	MODEL: str

	def get_url(self) -> str:
		return f"http://{self.HOST}:{self.PORT}"

	model_config = BASE_MODEL_CONFIG | SettingsConfigDict(env_prefix="EMBEDDING_")
