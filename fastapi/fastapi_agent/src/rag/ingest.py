import chromadb
from langchain_chroma import Chroma

from rag.config import COLLECTION_NAME, PERSIST_DIRECTORY
from rag.documents import load_documents, split_documents
from rag.embeddings import get_embeddings


def ingest_documents() -> int:
    """문서를 읽고 청킹·임베딩하여 컬렉션을 새로 만든다."""
    documents = load_documents()
    chunks = split_documents(documents)
    embeddings = get_embeddings()
    client = chromadb.PersistentClient(path=PERSIST_DIRECTORY)

    existing_names = [collection.name for collection in client.list_collections()]
    if COLLECTION_NAME in existing_names:
        client.delete_collection(COLLECTION_NAME)

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        client=client,
    )
    return len(chunks)


def main() -> None:
    count = ingest_documents()
    print(f"AI Brief 9월호: {count}개 청크 저장 완료")


if __name__ == "__main__":
    main()
