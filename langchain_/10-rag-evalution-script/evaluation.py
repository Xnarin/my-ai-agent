from __future__ import annotations

import statistics
from typing import Any


def file_hit_at_k(documents: list[dict], case: dict, k: int) -> int:
    return int(
        any(
            document["source"] == case["target_file_name"]
            for document in documents[:k]
        )
    )


def page_hit_at_k(documents: list[dict], case: dict, k: int) -> int:
    return int(
        any(
            document["source"] == case["target_file_name"]
            and document["page_no"] == case["target_page_no"]
            for document in documents[:k]
        )
    )


def reciprocal_rank(documents: list[dict], case: dict) -> float:
    for document in documents:
        if (
            document["source"] == case["target_file_name"]
            and document["page_no"] == case["target_page_no"]
        ):
            return 1 / document["rank"]
    return 0.0


def attach_retrieval_metrics(row: dict[str, Any], case: dict) -> dict[str, Any]:
    documents = row["documents"]
    return {
        **row,
        **{f"target_file_hit_{k}": file_hit_at_k(documents, case, k) for k in (1, 3, 5)},
        **{f"target_page_hit_{k}": page_hit_at_k(documents, case, k) for k in (1, 3, 5)},
        "reciprocal_rank": reciprocal_rank(documents, case),
    }


def summarize_retrieval(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    summary = {}
    strategies = list(dict.fromkeys(row["strategy"] for row in rows))
    for strategy in strategies:
        selected = [row for row in rows if row["strategy"] == strategy]
        summary[strategy] = {
            "count": len(selected),
            **{
                f"target_file_hit_{k}": round(
                    statistics.mean(row[f"target_file_hit_{k}"] for row in selected), 4
                )
                for k in (1, 3, 5)
            },
            **{
                f"target_page_hit_{k}": round(
                    statistics.mean(row[f"target_page_hit_{k}"] for row in selected), 4
                )
                for k in (1, 3, 5)
            },
            "mrr": round(statistics.mean(row["reciprocal_rank"] for row in selected), 4),
            "avg_latency_ms": round(
                statistics.mean(row["retrieval_latency_ms"] for row in selected), 2
            ),
        }
    return summary


def collect_retrieval_misses(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    metric_names = [
        *(f"target_file_hit_{k}" for k in (1, 3, 5)),
        *(f"target_page_hit_{k}" for k in (1, 3, 5)),
    ]
    misses = []
    for row in rows:
        missed_metrics = [name for name in metric_names if row[name] == 0]
        if not missed_metrics:
            continue
        misses.append(
            {
                "experiment": row["experiment"],
                "strategy": row["strategy"],
                "query_index": row["query_index"],
                "query_id": row["query_id"],
                "question": row["question"],
                "target_file_name": row["target_file_name"],
                "target_page_no": row["target_page_no"],
                "missed_metrics": missed_metrics,
                "documents": row["documents"],
            }
        )
    return misses
