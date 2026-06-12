import pandas as pd
import pdfplumber
from langchain_community.document_loaders import PyPDFLoader, UnstructuredWordDocumentLoader
from langchain_core.documents import Document

from src.rag.loaders.base import BaseLoader


def _clean_text(text: str) -> str:
	return " ".join(text.replace("\n", " ").split())


class PdfLoader(BaseLoader):
	def load(self) -> list[Document]:
		documents: list[Document] = []

		# основной текст берем старым проверенным способом
		text_docs = PyPDFLoader(file_path=self.file_path).load()
		for doc in text_docs:
			doc.metadata["type"] = "text"
		documents.extend(text_docs)

		# таблицы извлекаем отдельно (pdfplumber)
		table_idx = 0
		with pdfplumber.open(self.file_path) as pdf:
			for page_num, page in enumerate(pdf.pages):
				tables = page.extract_tables() or []
				for table in tables:
					if not table or not any(row for row in table):
						continue
					rows = []
					for row in table:
						if row and any(cell and str(cell).strip() for cell in row):
							cleaned_row = [_clean_text(str(cell)) if cell else "" for cell in row]
							rows.append(" | ".join(cleaned_row))
					if not rows:
						continue

					table_text = "Таблица:\n" + "\n".join(rows)
					metadata = {
						"source": self.file_path,
						"type": "table",
						"page": page_num + 1,
						"table_index": table_idx,
					}
					documents.append(Document(page_content=table_text, metadata=metadata))
					table_idx += 1

		return documents


# пока не работает
class WordLoader(BaseLoader):
	def load(self) -> list[Document]:
		return UnstructuredWordDocumentLoader(file_path=self.file_path).load()


class ExcelLoader(BaseLoader):
	def load(self) -> list[Document]:
		sheets: dict = pd.read_excel(self.file_path, sheet_name=None, header=0)

		documents = []
		for sheet_name, df in sheets.items():
			df = df.dropna(how="all").reset_index(drop=True)
			if df.empty:
				continue

			# убираем Unnamed-колонки (артефакт pandas когда нет заголовка)
			columns = [
				str(col).strip() if not str(col).startswith("Unnamed") else ""
				for col in df.columns
			]

			for row_idx, row in df.iterrows():
				parts = []
				for col_name, value in zip(columns, row.values):
					if pd.isna(value):
						continue
					value_str = _clean_text(str(value))
					if not value_str:
						continue
					parts.append(f"{col_name}: {value_str}" if col_name else value_str)

				if not parts:
					continue

				# каждая строка — одно читаемое предложение для модели
				content = f"Лист: {sheet_name}. " + ". ".join(parts) + "."
				documents.append(Document(
					page_content=content,
					metadata={
						"source": self.file_path,
						"type": "table",
						"sheet": sheet_name,
						"row": int(row_idx),
					},
				))

		return documents


# оставляем алиас для обратной совместимости
TableLoader = ExcelLoader
