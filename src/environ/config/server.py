from pydantic_settings import BaseSettings, SettingsConfigDict

from src.environ.base import BASE_MODEL_CONFIG


class Server(BaseSettings):
	HOST: str
	PORT: int
	USER: str
	PASSWORD: str
	DB: str

	def get_url(self) -> str:
		return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"

	model_config = BASE_MODEL_CONFIG | SettingsConfigDict(env_prefix="PSQL_")
