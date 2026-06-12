from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.rag.loaders.base import BaseLoader
from src.rag.loaders.loaders import ExcelLoader, PdfLoader, WordLoader

CHUNK_SIZE = 700

TEXT_SPLITTER = RecursiveCharacterTextSplitter(
	chunk_size=CHUNK_SIZE,
	chunk_overlap=120,
	add_start_index=True,
)


def select_loader(file_type) -> type[BaseLoader] | None:
	match file_type:
		case "pdf":
			return PdfLoader
		case "doc" | "docx":
			return WordLoader
		case "xls" | "xlsx":
			return ExcelLoader

	return None


def table_text_spliter(docs: list[Document], separator: str = " | ") -> list[Document]:
	"""
	Разбивает слишком длинные Document'ы (из таблиц) по самой длинной колонке.
	Возвращает обновлённый список документов.
	"""
	new_docs_list = []

	for doc in docs:
		if len(doc.page_content) <= CHUNK_SIZE:
			new_docs_list.append(doc)
			continue

		parts = doc.page_content.split(separator)
		if len(parts) <= 1:
			new_docs_list.append(doc)
			continue

		lengths = [len(part) for part in parts]
		longest_idx = lengths.index(max(lengths))

		if lengths[longest_idx] <= CHUNK_SIZE:
			new_docs_list.append(doc)
			continue

		longest_part = parts[longest_idx]
		chunks = TEXT_SPLITTER.split_text(longest_part)

		for chunk in chunks:
			new_parts = parts.copy()
			new_parts[longest_idx] = chunk
			new_content = separator.join(new_parts)
			new_docs_list.append(Document(page_content=new_content, metadata=doc.metadata))

	return new_docs_list
