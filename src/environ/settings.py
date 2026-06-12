from pydantic import Field
from pydantic_settings import BaseSettings

from src.environ.base import BASE_MODEL_CONFIG
from src.environ.config.embedding import Embedding
from src.environ.config.llm import LLMSettings
from src.environ.config.server import Server
from src.environ.config.telegram import TelegramSettings
from src.environ.config.vector_store import VectorStore


class Settings(BaseSettings):
	model_config = BASE_MODEL_CONFIG

	SERVER: Server | None = None
	VECTOR_STORE: VectorStore = Field(default_factory=VectorStore)
	LLM: LLMSettings = Field(default_factory=LLMSettings)
	EMBEDDING: Embedding = Field(default_factory=Embedding)
	TELEGRAM: TelegramSettings = Field(default_factory=TelegramSettings)


settings = Settings()
