from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai.types import HttpOptions, HttpRetryOptions
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from chunking import create_chunks
from comparison import compare_results
from config import PROJECT_DIR, ROOT_DIR, load_config
from data_loader import load_documents, load_evaluation_cases
from evaluation import (
    attach_retrieval_metrics,
    collect_retrieval_misses,
    summarize_retrieval,
)
from storage import read_jsonl, save_run_config, write_json, write_jsonl


def run_experiment(config: dict[str, Any], limit: int | None, dry_run: bool) -> None:
    documents = load_documents(config["data"]["documents_dir"])
    cases = load_evaluation_cases(config["data"]["evaluation_path"], limit)
    chunks = create_chunks(documents, config["chunking"])
    output_dir = config["output_dir"] / config["name"]

    print(f"실험: {config['name']}")
    print(f"설명: {config['description']}")
    print(f"문서: {len(documents)}개 / 평가: {len(cases)}개")
    print(
        f"청킹: {config['chunking']['strategy']}, "
        f"size={config['chunking']['chunk_size']}, "
        f"overlap={config['chunking']['chunk_overlap']}"
    )
    print(f"검색: {', '.join(config['retrieval']['strategies'])}, k={config['retrieval']['k']}")
    if dry_run:
        print("dry-run이므로 API를 호출하거나 결과를 저장하지 않습니다.")
        return

    from retrieval import build_searches, serialize_documents

    write_jsonl(
        output_dir / "chunks.jsonl",
        [
            {
                "chunk_id": chunk.metadata["chunk_id"],
                "source": chunk.metadata["source"],
                "page_no": chunk.metadata["page_no"],
                "content": chunk.page_content,
                "metadata": chunk.metadata,
            }
            for chunk in chunks
        ],
    )
    embeddings = GoogleGenerativeAIEmbeddings(model=config["embedding"]["model"])
    retry_client = genai.Client(
        http_options=HttpOptions(
            retry_options=HttpRetryOptions(
                attempts=8,  # 최초 요청 포함 총 8회
                initial_delay=2.0,  # 첫 재시도 대기 시간
                max_delay=60.0,  # 최대 대기 시간
                exp_base=2,  # 2초, 4초, 8초 순으로 대기 시간 증가
                jitter=1.0,  # 동시 재시도 요청을 분산하는 무작위 지연
            )
        )
    )
    embeddings.client = retry_client
    searches = build_searches(
        chunks=chunks,
        config=config["retrieval"],
        embeddings=embeddings,
        collection_name=config["name"].replace("-", "_"),
        persist_dir=PROJECT_DIR / "chroma_db",
    )

    results: list[dict[str, Any]] = []
    for strategy, search in searches.items():
        for position, case in enumerate(cases, start=1):
            question = str(case["question"])
            started = time.perf_counter()
            retrieved = serialize_documents(search(question))
            latency_ms = round((time.perf_counter() - started) * 1000, 2)
            row = attach_retrieval_metrics(
                {
                    "experiment": config["name"],
                    "strategy": strategy,
                    "query_index": position,
                    "query_id": case["case_id"],
                    "question": question,
                    "target_answer": case["target_answer"],
                    "target_file_name": case["target_file_name"],
                    "target_page_no": case["target_page_no"],
                    "context_type": case.get("context_type"),
                    "retrieval_latency_ms": latency_ms,
                    "documents": retrieved,
                },
                case,
            )
            results.append(row)
            if position % 5 == 0 or position == len(cases):
                status = "검색 완료" if position == len(cases) else "검색 중"
                print(f"[{strategy}] {position}/{len(cases)}개 문항 {status}")

    metrics = summarize_retrieval(results)
    write_jsonl(output_dir / "retrieval.jsonl", results)
    write_jsonl(
        output_dir / "retrieval_misses.jsonl",
        collect_retrieval_misses(results),
    )
    write_json(output_dir / "retrieval_metrics.json", metrics)
    save_run_config(output_dir / "run.json", config)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"저장: {output_dir}")

def run_comparison(baseline_dir: str, candidate_dir: str, output_dir: str) -> None:
    baseline_path = Path(baseline_dir).resolve() / "retrieval.jsonl"
    candidate_path = Path(candidate_dir).resolve() / "retrieval.jsonl"
    summary, cases = compare_results(
        read_jsonl(baseline_path), read_jsonl(candidate_path)
    )
    destination = Path(output_dir).resolve()
    write_json(destination / "summary.json", summary)
    write_jsonl(destination / "cases.jsonl", cases)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="RAG 설정별 실험과 결과 비교")
    parser.add_argument("--config", help="실험 설정 JSON 경로")
    parser.add_argument("--limit", type=int, help="앞에서부터 일부 문항만 실행")
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 설정 확인")
    parser.add_argument("--compare", nargs=2, metavar=("BASELINE_DIR", "CANDIDATE_DIR"))
    parser.add_argument("--comparison-output", default="outputs/comparison")
    return parser


def main() -> None:
    load_dotenv(ROOT_DIR / ".env")
    args = build_parser().parse_args()
    if args.compare:
        run_comparison(*args.compare, args.comparison_output)
        return
    if not args.config:
        raise SystemExit("--config 또는 --compare를 지정하세요.")
    run_experiment(load_config(args.config), args.limit, args.dry_run)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as error:
        print(f"오류: {error}", file=sys.stderr)
        raise SystemExit(1) from error
