import asyncio

from langchain_ollama import OllamaEmbeddings

from src.environ.settings import settings


class EmbeddingHelper:
	def __init__(self):
		self._embeddings = OllamaEmbeddings(model=settings.EMBEDDING.MODEL, base_url=settings.EMBEDDING.get_url())

	async def embed_query(self, query: str) -> list[float]:
		loop = asyncio.get_running_loop()
		return await loop.run_in_executor(None, self._embeddings.embed_query, query)

	async def embed_documents(self, texts: list[str]):
		loop = asyncio.get_running_loop()
		return await loop.run_in_executor(None, self._embeddings.embed_documents, texts)
