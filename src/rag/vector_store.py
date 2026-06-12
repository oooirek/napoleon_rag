import uuid

from langchain_core.documents import Document
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.models import PointStruct

from src.environ.settings import settings

BATCH_SIZE = 50
VECTOR_SIZE = 1024


class VectorStoreClient:
	def __init__(self) -> None:
		self._client = AsyncQdrantClient(
			host=settings.VECTOR_STORE.HOST, port=settings.VECTOR_STORE.PORT, https=False, check_compatibility=False
		)

	async def is_collection_exists(self, collection_name: str) -> bool:
		return await self._client.collection_exists(collection_name=collection_name)

	# vector_size берется из EmbeddingHelper.get_vector_size(), но можно задать в ручную если знать размерность
	async def create_collection(self, collection_name: str, vector_size: int = VECTOR_SIZE) -> None:
		if await self._client.collection_exists(collection_name=collection_name):
			return
		await self._client.create_collection(
			collection_name=collection_name,
			vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
		)

	async def add_documents(self, collection_name: str, docs: list[Document], vectors: list[list[float]]) -> None:

		batch = []
		for doc, vector in zip(docs, vectors, strict=True):
			batch.append(
				PointStruct(
					id=str(uuid.uuid4()),
					vector=vector,
					payload={"text": doc.page_content, "metadata": doc.metadata},
				)
			)

			if len(batch) >= BATCH_SIZE:
				await self._client.upsert(collection_name=collection_name, points=batch)
				batch.clear()

		if batch:
			await self._client.upsert(collection_name=collection_name, points=batch)

	async def search(self, collection_name: str, query_vector: list[float], k: int = 4):
		results = await self._client.query_points(
			collection_name=collection_name,
			query=query_vector,
			limit=k,
			with_payload=True,
		)

		return results.points

	async def delete_documents(self, collection_name: str, documents: list[Document]) -> None:
		pass

	async def remove_collection(self, collection_name) -> None:
		await self._client.delete_collection(collection_name)
