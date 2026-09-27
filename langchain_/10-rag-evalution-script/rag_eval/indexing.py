"""문서 로드 → 청킹 → 벡터 스토어 구축.

08-rag-pipeline.ipynb / 09-rag-search-advanced.ipynb에서 사용한 패턴을 그대로
따른다: 파일별로 로드한 뒤 chunk_id(파일명:인덱스)를 부여하여 Hybrid Search의
EnsembleRetriever가 청크를 구분할 수 있게 한다.
"""

from __future__ import annotations

from pathlib import Path

import chromadb
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

TEXT_SUFFIXES = {".md", ".txt"}


def load_documents_by_file(document_glob: str, base_dir: Path) -> list[tuple[Path, list[Document]]]:
    """glob 패턴에 맞는 파일을 각각 로드한다. (경로, 페이지/문서 리스트) 튜플을 반환한다."""
    paths = sorted(base_dir.glob(document_glob))
    if not paths:
        raise FileNotFoundError(
            f"'{document_glob}' 패턴에 맞는 문서를 {base_dir}에서 찾지 못했습니다."
        )

    loaded_by_file = []
    for path in paths:
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            docs = PyPDFLoader(str(path)).load()
        elif suffix in TEXT_SUFFIXES:
            docs = TextLoader(str(path), encoding="utf-8").load()
        else:
            raise ValueError(f"지원하지 않는 문서 형식입니다: {path}")
        # golden set의 source/target_file_name과 비교할 수 있도록 파일명으로 통일한다.
        for doc in docs:
            doc.metadata["source"] = path.name
        loaded_by_file.append((path, docs))
    return loaded_by_file


def chunk_documents(
    loaded_by_file: list[tuple[Path, list[Document]]],
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    chunks: list[Document] = []
    for path, docs in loaded_by_file:
        file_chunks = splitter.split_documents(docs)
        for chunk_index, chunk in enumerate(file_chunks):
            chunk.metadata["chunk_id"] = f"{path.stem}:{chunk_index}"
        chunks.extend(file_chunks)
    return chunks


def build_vectorstore(
    chunks: list[Document],
    embeddings,
    persist_dir: str,
    collection_name: str,
    rebuild_index: bool,
) -> Chroma:
    client = chromadb.PersistentClient(path=persist_dir)
    existing_names = [c.name for c in client.list_collections()]

    if rebuild_index:
        if collection_name in existing_names:
            client.delete_collection(collection_name)
        return Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=collection_name,
            client=client,
        )

    if collection_name not in existing_names:
        raise ValueError(
            f"컬렉션 '{collection_name}'이 '{persist_dir}'에 없습니다. "
            "config에서 rebuild_index를 true로 설정하세요."
        )
    stored_count = client.get_collection(collection_name).count()
    if stored_count != len(chunks):
        raise ValueError(
            f"컬렉션 '{collection_name}'의 저장된 청크 수({stored_count})가 "
            f"현재 문서에서 만들어진 청크 수({len(chunks)})와 다릅니다. "
            "이전 실행이 중간에 실패(예: 429)해 컬렉션이 불완전하게 남아있을 수 "
            "있습니다. config에서 rebuild_index를 true로 설정해 다시 색인하세요."
        )
    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        client=client,
    )
