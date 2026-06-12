from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.rag.container import RAGContainer
from src.rag.utils import select_loader, table_text_spliter

TEXT_SPLITTER = RecursiveCharacterTextSplitter(
	chunk_size=700,
	chunk_overlap=120,
	add_start_index=True,
)
TABLE_SPLITTER = RecursiveCharacterTextSplitter(
	chunk_size=400,
	chunk_overlap=60,
	add_start_index=True,
)


class DocumentIngestion:
	def __init__(self, container: RAGContainer) -> None:
		self.vector_store_client = container.vector_store
		self.embeddings_client = container.embeddings

	async def ingest(self, collection_name: str, file_path: str, file_extension: str) -> int:
		loader_class = select_loader(file_extension)
		current_loader = loader_class(file_path)

		docs = current_loader.load()

		if file_extension in ("xls", "xlsx"):
			pass  # каждая строка уже один чанк, дополнительный сплиттер не нужен
		elif file_extension == "pdf":
			text_docs = [doc for doc in docs if doc.metadata.get("type") != "table"]
			table_docs = [doc for doc in docs if doc.metadata.get("type") == "table"]

			text_docs = TEXT_SPLITTER.split_documents(text_docs) if text_docs else []
			table_docs = TABLE_SPLITTER.split_documents(table_docs) if table_docs else []

			docs = text_docs + table_docs
		else:
			docs = TEXT_SPLITTER.split_documents(docs)

		for i, doc in enumerate(docs):
			doc.metadata.update({"source": file_path, "chunk_id": i})

		texts = [doc.page_content for doc in docs]
		vectors = await self.embeddings_client.embed_documents(texts)

		await self.vector_store_client.add_documents(
			collection_name=collection_name,
			docs=docs,
			vectors=vectors,
		)
		return len(docs)
