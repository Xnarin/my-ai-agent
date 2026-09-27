from __future__ import annotations

from pathlib import Path
from typing import Callable

import chromadb
from kiwipiepy import Kiwi
from langchain_chroma import Chroma
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document


kiwi = Kiwi()


def kiwi_tokenize(text: str) -> list[str]:
    tokens = kiwi.tokenize(text)
    return [
        token.form.lower()
        for token in tokens
        if token.tag.startswith(("N", "V", "M", "X"))
        or token.tag in {"SL", "SN"}
    ]


def build_searches(
    chunks: list[Document],
    config: dict,
    embeddings,
    collection_name: str,
    persist_dir: Path,
) -> dict[str, Callable[[str], list[Document]]]:
    strategies = config["strategies"]
    k = config["k"]
    searches: dict[str, Callable[[str], list[Document]]] = {}

    bm25 = None
    if set(strategies) & {"bm25", "hybrid"}:
        bm25 = BM25Retriever.from_documents(
            chunks,
            preprocess_func=kiwi_tokenize,
            k=config["fetch_k"],
        )
        if "bm25" in strategies:
            searches["bm25"] = lambda question: bm25.invoke(question)[:k]

    vectorstore = None
    if set(strategies) & {"similarity", "mmr", "hybrid"}:
        client = chromadb.PersistentClient(path=str(persist_dir))
        existing = [collection.name for collection in client.list_collections()]
        if collection_name in existing:
            client.delete_collection(collection_name)
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=collection_name,
            client=client,
        )

    if "similarity" in strategies:
        searches["similarity"] = (
            lambda question: vectorstore.similarity_search(question, k=k)
        )
    if "mmr" in strategies:
        searches["mmr"] = (
            lambda question: vectorstore.max_marginal_relevance_search(
                question,
                k=k,
                fetch_k=config["fetch_k"],
                lambda_mult=config["lambda_mult"],
            )
        )
    if "hybrid" in strategies:
        vector_retriever = vectorstore.as_retriever(
            search_kwargs={"k": config["fetch_k"]}
        )
        hybrid = EnsembleRetriever(
            retrievers=[vector_retriever, bm25],
            weights=config["weights"],
            id_key="chunk_id",
        )
        searches["hybrid"] = lambda question: hybrid.invoke(question)[:k]

    return {strategy: searches[strategy] for strategy in strategies}


def serialize_documents(documents: list[Document]) -> list[dict]:
    return [
        {
            "rank": rank,
            "chunk_id": document.metadata.get("chunk_id"),
            "source": document.metadata.get("source"),
            "page_no": document.metadata.get("page_no"),
            "content": document.page_content,
            "metadata": document.metadata,
        }
        for rank, document in enumerate(documents, start=1)
    ]
