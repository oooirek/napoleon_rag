from abc import ABC, abstractmethod

from langchain_core.documents import Document


class BaseLoader(ABC):
	def __init__(self, file_path):
		self.file_path = file_path

	@abstractmethod
	def load(self) -> list[Document]: ...
