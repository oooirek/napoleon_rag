from langchain_core.documents import Document

from src.rag.embedding import EmbeddingHelper
from src.rag.vector_store import VectorStoreClient


class CustomRetriever:
	def __init__(self, vector_store: VectorStoreClient, embeddings: EmbeddingHelper):
		self.vector_store_client = vector_store
		self.embeddings_client = embeddings

	async def invoke(self, collection_name: str, query: str, k: int = 4) -> list[Document]:
		query_vector = await self.embeddings_client.embed_query(query)
		results = await self.vector_store_client.search(
			collection_name=collection_name,
			query_vector=query_vector,
			k=k,
		)

		docs = [
			Document(
				page_content=res.payload.get("text", ""),
				metadata=res.payload.get("metadata", {}),
			)
			for res in results
		]

		return docs
