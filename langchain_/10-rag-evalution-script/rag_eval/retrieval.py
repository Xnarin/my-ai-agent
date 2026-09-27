"""검색 전략별 검색기 빌더.

09-rag-search-advanced.ipynb / 10-rag-evaluation.ipynb에서 사용한 네 가지
전략(similarity, mmr, bm25, hybrid)을 config 값으로 조립한다. 반환값은 항상
`query(str) -> list[Document]` 형태의 함수이며, 결과 개수는 config.k로 맞춘다.
"""

from __future__ import annotations

from typing import Callable

from kiwipiepy import Kiwi
from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from rag_eval.config import RunConfig

SearchFn = Callable[[str], list[Document]]

_kiwi = Kiwi()


def kiwi_tokenize(text: str) -> list[str]:
    """BM25용 형태소 분석 토큰화. 명사/동사/형용사/수사/외국어 토큰만 사용한다."""
    tokens = _kiwi.tokenize(text)
    return [
        token.form.lower()
        for token in tokens
        if token.tag.startswith(("N", "V", "M", "X")) or token.tag in {"SL", "SN"}
    ]


def build_search_fn(config: RunConfig, vectorstore, chunks: list[Document]) -> SearchFn:
    strategy = config.search_strategy

    if strategy == "similarity":
        retriever = vectorstore.as_retriever(search_kwargs={"k": config.k})
        return retriever.invoke

    if strategy == "mmr":
        retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": config.k,
                "fetch_k": config.fetch_k,
                "lambda_mult": config.lambda_mult,
            },
        )
        return retriever.invoke

    if strategy == "bm25":
        retriever = BM25Retriever.from_documents(
            chunks, preprocess_func=kiwi_tokenize, k=config.k
        )
        return retriever.invoke

    if strategy == "hybrid":
        pool_size = max(config.k, config.fetch_k)
        vector_retriever = vectorstore.as_retriever(search_kwargs={"k": pool_size})
        bm25_retriever = BM25Retriever.from_documents(
            chunks, preprocess_func=kiwi_tokenize, k=pool_size
        )
        ensemble = EnsembleRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            weights=config.weights,
            id_key="chunk_id",
        )
        k = config.k
        return lambda query: ensemble.invoke(query)[:k]

    raise ValueError(f"알 수 없는 search_strategy입니다: {strategy}")
