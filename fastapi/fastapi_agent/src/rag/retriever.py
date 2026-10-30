from langchain_core.vectorstores import VectorStoreRetriever

from rag.vectorstore import get_vectorstore


def get_retriever(k: int = 4) -> VectorStoreRetriever:
    return get_vectorstore().as_retriever(search_kwargs={"k": k})
