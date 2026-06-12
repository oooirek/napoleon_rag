from langchain_ollama import ChatOllama

from src.environ.settings import settings
from src.rag.embedding import EmbeddingHelper
from src.rag.vector_store import VectorStoreClient


class RAGContainer:
	llm = ChatOllama(model=settings.LLM.MODEL, base_url=settings.LLM.get_url())
	vector_store = VectorStoreClient()
	embeddings = EmbeddingHelper()

	"""
    тк они тяж и создал единые экземпляры
    """
