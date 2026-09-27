from __future__ import annotations

from typing import Any

from evaluation import summarize_retrieval


def compare_results(
    baseline_rows: list[dict[str, Any]], candidate_rows: list[dict[str, Any]]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    key = lambda row: (row["strategy"], str(row["query_id"]))
    baseline = {key(row): row for row in baseline_rows}
    candidate = {key(row): row for row in candidate_rows}
    shared_keys = baseline.keys() & candidate.keys()
    if not shared_keys:
        raise ValueError("두 결과에 공통 strategy와 query_id가 없습니다.")
    if baseline.keys() != candidate.keys():
        missing_baseline = sorted(candidate.keys() - baseline.keys())
        missing_candidate = sorted(baseline.keys() - candidate.keys())
        raise ValueError(
            "동일한 전략과 평가 문항으로 실행한 결과만 비교할 수 있습니다. "
            f"baseline 누락={len(missing_baseline)}, candidate 누락={len(missing_candidate)}"
        )

    cases: list[dict[str, Any]] = []
    for strategy, query_id in sorted(shared_keys):
        before = baseline[(strategy, query_id)]
        after = candidate[(strategy, query_id)]
        if before["question"] != after["question"]:
            raise ValueError(f"query_id가 같지만 질문이 다릅니다: {query_id}")
        delta = round(after["reciprocal_rank"] - before["reciprocal_rank"], 6)
        cases.append(
            {
                "strategy": strategy,
                "query_id": before["query_id"],
                "question": before["question"],
                "baseline_rr": before["reciprocal_rank"],
                "candidate_rr": after["reciprocal_rank"],
                "rr_delta": delta,
                "change": "improved" if delta > 0 else "degraded" if delta < 0 else "same",
                "baseline_documents": before["documents"],
                "candidate_documents": after["documents"],
            }
        )

    baseline_metrics = summarize_retrieval([baseline[item] for item in shared_keys])
    candidate_metrics = summarize_retrieval([candidate[item] for item in shared_keys])
    metric_names = [
        *(f"target_file_hit_{k}" for k in (1, 3, 5)),
        *(f"target_page_hit_{k}" for k in (1, 3, 5)),
        "mrr", "avg_latency_ms",
    ]
    delta = {
        strategy: {
            metric: round(candidate_metrics[strategy][metric] - baseline_metrics[strategy][metric], 4)
            for metric in metric_names
        }
        for strategy in baseline_metrics.keys() & candidate_metrics.keys()
    }
    summary = {
        "baseline_metrics": baseline_metrics,
        "candidate_metrics": candidate_metrics,
        "delta": delta,
        "improved_count": sum(row["change"] == "improved" for row in cases),
        "degraded_count": sum(row["change"] == "degraded" for row in cases),
        "same_count": sum(row["change"] == "same" for row in cases),
    }
    return summary, cases
