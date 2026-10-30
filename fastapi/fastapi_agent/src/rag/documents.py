from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from rag.config import CHUNK_OVERLAP, CHUNK_SIZE, PDF_PATH


def load_documents() -> list[Document]:
    """AI Brief 9월호를 페이지별로 읽는다."""
    documents = PyPDFLoader(str(PDF_PATH)).load()
    for document in documents:
        document.metadata["source"] = PDF_PATH.name
        document.metadata["page_number"] = document.metadata["page"] + 1
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    """문서를 나누고 청크마다 ID를 부여한다."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = str(index)
    return chunks
