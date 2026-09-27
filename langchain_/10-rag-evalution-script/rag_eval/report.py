"""실험 결과 저장과 비교 테이블 생성.

CONFIG_INPUT_OUTPUT_GUIDE.md의 output 항목(사용한 input + 실험 결과)을 그대로
파일로 남긴다. 실험마다 고유한 디렉터리에 저장하므로 같은 실험을 다시 재현하고
여러 실험을 비교할 수 있다.
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

TRACKED_PACKAGES = [
    "langchain",
    "langchain-core",
    "langchain-chroma",
    "langchain-community",
    "langchain-classic",
    "langchain-google-genai",
    "chromadb",
    "google-genai",
    "kiwipiepy",
    "rank-bm25",
    "pydantic",
]


def make_output_dir(result_root: Path, experiment_name: str, timestamp: str) -> Path:
    out_dir = result_root / f"{experiment_name}_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir


def _write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    lines = [json.dumps(row, ensure_ascii=False) for row in rows]
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def build_run_info(config: dict, base_dir: Path, timestamp: str) -> dict:
    """실행 환경과 입력 파일 해시를 기록한다.

    같은 config로 다시 실행했을 때 실제로 같은 문서·평가 데이터를 사용했는지
    확인하거나, 패키지 버전 차이로 결과가 달라졌는지 추적하는 데 사용한다.
    """
    eval_path = Path(config["eval_data_path"])
    eval_path = eval_path if eval_path.is_absolute() else base_dir / eval_path
    document_paths = sorted(base_dir.glob(config["document_glob"]))

    combined = hashlib.sha256()
    for path in document_paths:
        combined.update(_hash_file(path).encode("utf-8"))

    packages = {}
    for name in TRACKED_PACKAGES:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            continue

    return {
        "timestamp": timestamp,
        "python_version": platform.python_version(),
        "packages": packages,
        "input_hashes": {
            "eval_data": _hash_file(eval_path) if eval_path.exists() else None,
            "document_count": len(document_paths),
            "documents_combined": combined.hexdigest()[:16],
        },
    }


def render_summary_md(experiment: dict) -> str:
    config = experiment["config"]
    retrieval = experiment["retrieval"]
    generation = experiment.get("generation")
    lines = [
        f"# {config['experiment_name']}",
        "",
        "## 사용한 input",
        "",
        f"- 문서: `{config['document_glob']}`",
        f"- 평가 데이터: `{config['eval_data_path']}`",
        f"- 청킹: chunk_size={config['chunk_size']}, chunk_overlap={config['chunk_overlap']}",
        f"- 임베딩 모델: `{config['embedding_model']}`",
        (
            f"- 검색 전략: `{config['search_strategy']}` "
            f"(k={config['k']}, fetch_k={config['fetch_k']}, "
            f"lambda_mult={config['lambda_mult']}, weights={config['weights']})"
        ),
        f"- 생성 모델: `{config['generation_model']}` / 평가 모델: `{config['eval_model']}`",
        f"- 생성 평가 지표: {config['generation_metrics']}",
        "",
        "## 검색 평가 결과",
        "",
        "| 지표 | 값 |",
        "|---|---|",
    ]
    for key, value in retrieval["summary"].items():
        lines.append(f"| {key} | {value:.3f} |" if isinstance(value, float) else f"| {key} | {value} |")

    if retrieval.get("by_difficulty"):
        lines += ["", "### 난이도별", "", "| 난이도 | hit@1 | mrr | latency_ms |", "|---|---|---|---|"]
        for difficulty, summary in retrieval["by_difficulty"].items():
            lines.append(
                f"| {difficulty} | {summary.get('hit@1', 0):.3f} | {summary.get('mrr', 0):.3f} "
                f"| {summary.get('latency_ms', 0):.1f} |"
            )

    if generation:
        lines += ["", "## 답변 생성 평가 결과", ""]
        if generation.get("citation_check"):
            lines += ["### 인용 규칙 검사", "", "| 지표 | 값 |", "|---|---|"]
            for key, value in generation["citation_check"].items():
                lines.append(f"| {key} | {value:.3f} |" if isinstance(value, float) else f"| {key} | {value} |")
        if generation.get("llm_judge"):
            lines += ["", "### LLM-as-Judge", "", "| 지표 | 값 |", "|---|---|"]
            for key, value in generation["llm_judge"].items():
                lines.append(f"| {key} | {value:.3f} |" if isinstance(value, float) else f"| {key} | {value} |")
        if generation.get("ragas"):
            lines += ["", "### RAGAS", "", "| 지표 | 값 |", "|---|---|"]
            for key, value in generation["ragas"].items():
                lines.append(f"| {key} | {value:.3f} |" if isinstance(value, float) else f"| {key} | {value} |")

    lines += [
        "",
        "## 비용/시간 (trade-off)",
        "",
        f"- 검색 latency: {retrieval['summary'].get('latency_ms', 0):.1f} ms/문항",
    ]
    if generation and generation.get("citation_check"):
        lines.append(
            f"- 답변 생성 latency: {generation['citation_check'].get('avg_latency_ms', 0):.1f} ms/문항"
        )
    if generation and generation.get("llm_judge"):
        lines.append(
            f"- Judge 평가 latency: {generation['llm_judge'].get('avg_latency_ms', 0):.1f} ms/문항"
        )
    return "\n".join(lines) + "\n"


def save_retrieval_misses(output_dir: Path, experiment: dict) -> None:
    """정답 출처를 모두 찾지 못한 문항(recall@k < 1)을 실패 분석용으로 따로 남긴다."""
    k = experiment["config"]["k"]
    rows = experiment["retrieval"]["rows"]
    misses = [row for row in rows if row.get(f"recall@{k}", 1.0) < 1.0]
    _write_jsonl(output_dir / "retrieval_misses.jsonl", misses)


def save_experiment(output_dir: Path, experiment: dict, run_info: dict | None = None) -> None:
    _write_json(output_dir / "config.json", experiment["config"])
    _write_json(output_dir / "retrieval_rows.json", experiment["retrieval"]["rows"])
    _write_json(
        output_dir / "retrieval_summary.json",
        {"summary": experiment["retrieval"]["summary"], "by_difficulty": experiment["retrieval"].get("by_difficulty")},
    )
    save_retrieval_misses(output_dir, experiment)
    generation = experiment.get("generation")
    if generation:
        _write_json(output_dir / "generation_rows.json", generation.get("rows", []))
        _write_json(
            output_dir / "generation_summary.json",
            {
                "citation_check": generation.get("citation_check"),
                "llm_judge": generation.get("llm_judge"),
                "ragas": generation.get("ragas"),
            },
        )
    if run_info is not None:
        _write_json(output_dir / "run_info.json", run_info)
    (output_dir / "summary.md").write_text(render_summary_md(experiment), encoding="utf-8")


def assert_comparable(experiments: list[dict]) -> None:
    """실험들이 같은 평가 문항 집합을 사용했는지 확인한다.

    golden set이 다르거나 --limit이 달라 문항 집합이 다르면 지표를 그대로
    비교할 수 없으므로, 비교 테이블을 만들기 전에 미리 걸러낸다.
    """
    if len(experiments) < 2:
        return
    labeled_id_sets = [
        (
            experiment["config"]["experiment_name"],
            frozenset(row["id"] for row in experiment["retrieval"]["rows"]),
        )
        for experiment in experiments
    ]
    _, reference_ids = labeled_id_sets[0]
    if all(ids == reference_ids for _, ids in labeled_id_sets[1:]):
        return
    details = ", ".join(f"{name}({len(ids)}문항)" for name, ids in labeled_id_sets)
    raise ValueError(
        "실험마다 평가 문항 집합이 다릅니다. 같은 golden set과 같은 --limit으로 "
        f"다시 실행한 뒤 비교하세요. ({details})"
    )


def build_comparison_table(experiments: list[dict]) -> list[dict]:
    """여러 실험의 요약 지표를 한 표로 모은다."""
    rows = []
    for experiment in experiments:
        config = experiment["config"]
        retrieval_summary = experiment["retrieval"]["summary"]
        generation = experiment.get("generation") or {}
        citation = generation.get("citation_check") or {}
        judge = generation.get("llm_judge") or {}
        rows.append({
            "experiment_name": config["experiment_name"],
            "search_strategy": config["search_strategy"],
            "chunk_size": config["chunk_size"],
            "chunk_overlap": config["chunk_overlap"],
            "k": config["k"],
            "hit@1": retrieval_summary.get("hit@1", 0.0),
            "mrr": retrieval_summary.get("mrr", 0.0),
            f"recall@{config['k']}": retrieval_summary.get(f"recall@{config['k']}", 0.0),
            f"page_hit@{config['k']}": retrieval_summary.get(f"page_hit@{config['k']}"),
            "retrieval_latency_ms": retrieval_summary.get("latency_ms", 0.0),
            "valid_citation_rate": citation.get("valid_citation_rate"),
            "judge_average": judge.get("average"),
            "generation_latency_ms": citation.get("avg_latency_ms"),
        })
    return rows


def render_comparison_md(rows: list[dict]) -> str:
    if not rows:
        return "비교할 실험이 없습니다.\n"
    headers = list(rows[0].keys())
    lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for row in rows:
        values = []
        for header in headers:
            value = row[header]
            if isinstance(value, float):
                values.append(f"{value:.3f}")
            else:
                values.append("-" if value is None else str(value))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def save_comparison(output_dir: Path, rows: list[dict]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_json(output_dir / "comparison.json", rows)
    (output_dir / "comparison.md").write_text(render_comparison_md(rows), encoding="utf-8")

    import csv

    if rows:
        with (output_dir / "comparison.csv").open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
