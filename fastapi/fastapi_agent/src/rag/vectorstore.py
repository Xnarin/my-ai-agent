from langchain_chroma import Chroma

from rag.config import COLLECTION_NAME, PERSIST_DIRECTORY
from rag.embeddings import get_embeddings


def get_vectorstore() -> Chroma:
    """AI Brief 9월호가 저장된 벡터 DB를 연다."""
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=get_embeddings(),
        create_collection_if_not_exists=False,
    )
