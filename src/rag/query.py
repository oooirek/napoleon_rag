from langchain_core.prompts import ChatPromptTemplate

from src.rag.container import RAGContainer
from src.rag.retriever import CustomRetriever

PROMPT = ChatPromptTemplate.from_template(
	"""Ты — помощник, отвечающий ТОЛЬКО на русском языке. Использую ТОЛЬКО тот контекст который у тебя есть. 
	
    Контекст:
    {context}

    Вопрос:
    {question}

    Ответ (только на русском):"""
)


async def query_rag(container: RAGContainer, query: str, collection_name: str):
	retriever = CustomRetriever(vector_store=container.vector_store, embeddings=container.embeddings)

	docs = await retriever.invoke(collection_name, query, 7)
	context = "\n\n".join(doc.page_content for doc in docs)

	chain = PROMPT | container.llm
	response = chain.invoke({"context": context, "question": query})

	return response.content
