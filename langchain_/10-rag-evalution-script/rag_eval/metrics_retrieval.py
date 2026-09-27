"""검색 평가 지표: Hit@k, Precision@k, Recall@k, RR/MRR, Page Hit@k.

10-rag-evaluation.ipynb의 계산식(파일 단위)에 더해, golden set에 정답 페이지
(target_page)가 있는 경우 페이지 단위 Hit@k도 함께 계산한다. 파일 단위 적중은
같은 파일의 다른 페이지가 검색되어도 정답으로 인정하므로, 페이지 단위 지표는
더 엄격한 대리 지표로 사용한다.

evaluate_retrieval()은 검색된 Document를 case id별로도 반환한다. 답변 생성
단계에서 이 결과를 재사용하면 같은 실험 안에서 검색을 반복하지 않는다.
"""

from __future__ import annotations

import time


def hit_at_k(ranked: list[str], relevant: list[str], k: int) -> int:
    return int(bool(set(ranked[:k]) & set(relevant)))


def precision_at_k(ranked: list[str], relevant: list[str], k: int) -> float:
    selected = ranked[:k]
    if not selected:
        return 0.0
    hits = sum(source in relevant for source in selected)
    return hits / len(selected)


def recall_at_k(ranked: list[str], relevant: list[str], k: int) -> float:
    relevant_set = set(relevant)
    if not relevant_set:
        return 0.0
    hits = len(set(ranked[:k]) & relevant_set)
    return hits / len(relevant_set)


def reciprocal_rank(ranked: list[str], relevant: list[str]) -> float:
    relevant_set = set(relevant)
    for rank, source in enumerate(ranked, start=1):
        if source in relevant_set:
            return 1 / rank
    return 0.0


def page_hit_at_k(
    ranked_sources: list[str],
    ranked_pages: list[int | None],
    relevant_sources: list[str],
    target_page: int | None,
    k: int,
) -> int | None:
    """정답 파일의 정답 페이지가 상위 k개 안에 있으면 1, 없으면 0.

    target_page가 없으면(golden set에 페이지 정보가 없으면) None을 반환해
    집계에서 제외한다. PyPDFLoader의 'page' 메타데이터는 0부터 시작하므로
    사람이 보는 페이지 번호와 비교할 때 1을 더한다.
    """
    if target_page is None:
        return None
    relevant_set = set(relevant_sources)
    for source, page in zip(ranked_sources[:k], ranked_pages[:k]):
        if source in relevant_set and page is not None and (page + 1) == target_page:
            return 1
    return 0


def evaluate_retrieval(search_fn, cases: list[dict], k: int) -> dict:
    """전체 평가 문항에 검색 전략을 실행하고 문항별/요약 지표를 반환한다.

    반환값의 docs_by_case_id는 case id -> 상위 k개 Document 목록이며, 답변
    생성 단계에서 검색을 반복하지 않고 재사용하는 데 쓴다.
    """
    rows = []
    docs_by_case_id: dict = {}
    started = time.perf_counter()
    for case in cases:
        docs = search_fn(case["question"])
        top_docs = docs[:k]
        docs_by_case_id[case["id"]] = top_docs

        ranked_sources = [doc.metadata.get("source", "") for doc in top_docs]
        ranked_pages = [doc.metadata.get("page") for doc in top_docs]
        relevant = case["relevant_sources"]
        target_page = case.get("target_page")

        rows.append({
            "id": case["id"],
            "question": case["question"],
            "difficulty": case["difficulty"],
            "relevant": relevant,
            "target_page": target_page,
            "retrieved": ranked_sources,
            "hit@1": hit_at_k(ranked_sources, relevant, 1),
            "hit@3": hit_at_k(ranked_sources, relevant, 3),
            f"hit@{k}": hit_at_k(ranked_sources, relevant, k),
            f"precision@{k}": precision_at_k(ranked_sources, relevant, k),
            "recall@3": recall_at_k(ranked_sources, relevant, 3),
            f"recall@{k}": recall_at_k(ranked_sources, relevant, k),
            "mrr": reciprocal_rank(ranked_sources, relevant),
            "page_hit@1": page_hit_at_k(ranked_sources, ranked_pages, relevant, target_page, 1),
            "page_hit@3": page_hit_at_k(ranked_sources, ranked_pages, relevant, target_page, 3),
            f"page_hit@{k}": page_hit_at_k(ranked_sources, ranked_pages, relevant, target_page, k),
        })
    elapsed_ms = (time.perf_counter() - started) * 1000
    latency_ms = elapsed_ms / len(cases) if cases else 0.0
    return {
        "rows": rows,
        "docs_by_case_id": docs_by_case_id,
        "latency_ms": latency_ms,
        "total_ms": elapsed_ms,
    }


def _average(rows: list[dict], key: str) -> float:
    if not rows:
        return 0.0
    return sum(row[key] for row in rows) / len(rows)


def _average_ignore_none(rows: list[dict], key: str) -> float | None:
    values = [row[key] for row in rows if row.get(key) is not None]
    if not values:
        return None
    return sum(values) / len(values)


def summarize_retrieval(result: dict, k: int, rows: list[dict] | None = None) -> dict:
    rows = result["rows"] if rows is None else rows
    keys = ["hit@1", "hit@3", f"hit@{k}", f"precision@{k}", "recall@3", f"recall@{k}", "mrr"]
    summary = {"count": len(rows)}
    summary.update({key: _average(rows, key) for key in keys})

    page_keys = ["page_hit@1", "page_hit@3", f"page_hit@{k}"]
    page_eval_count = sum(1 for row in rows if row.get("target_page") is not None)
    if page_eval_count:
        summary["page_eval_count"] = page_eval_count
        summary.update({key: _average_ignore_none(rows, key) for key in page_keys})

    summary["latency_ms"] = result["latency_ms"]
    return summary


def summarize_by_difficulty(result: dict, k: int) -> dict:
    difficulties = sorted({row["difficulty"] for row in result["rows"]})
    return {
        difficulty: summarize_retrieval(
            result, k, [row for row in result["rows"] if row["difficulty"] == difficulty]
        )
        for difficulty in difficulties
    }
