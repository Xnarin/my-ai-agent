from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def create_chunks(
    documents: list[Document], config: dict
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config["chunk_size"],
        chunk_overlap=config["chunk_overlap"],
        separators=config["separators"],
    )
    chunks = splitter.split_documents(documents)
    for index, chunk in enumerate(chunks):
        source = chunk.metadata["source"]
        chunk.metadata["chunk_id"] = f"{source}:{index}"
        if config.get("include_source", False):
            chunk.page_content = f"[출처: {source}]\n{chunk.page_content}"
    return chunks
