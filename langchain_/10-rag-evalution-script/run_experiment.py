"""단일 RAG 실험을 실행한다.

사용 예시:
    python run_experiment.py --config configs/company_rules_similarity.json --dry-run
    python run_experiment.py --config configs/company_rules_similarity.json --limit 5
    python run_experiment.py --config configs/company_rules_similarity.json --search-strategy hybrid --k 8
    python run_experiment.py --config configs/public_similarity.json --no-run-generation

옵션 이름의 하이픈(-)은 Python에서 언더스코어(_)로 접근한다 (예: --chunk-size → args.chunk_size).
config 파일에 없는 값을 바꾸고 싶다면 config JSON을 직접 수정한다.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from rag_eval.config import RunConfig
from rag_eval.experiment import run_experiment
from rag_eval.report import build_run_info, make_output_dir, save_experiment

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_DIR = SCRIPT_DIR.parent  # langchain_ 폴더: data/, chroma_db/가 위치한 곳


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True, help="실험 설정 JSON 파일 경로")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR),
                         help="document_glob/eval_data_path 등 상대 경로의 기준 디렉터리")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="문서 로드·청킹과 문항 수만 확인한다. 임베딩 API를 호출하거나 결과를 저장하지 않는다.",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="golden set 앞쪽 N개 문항만 사용한다(검색·생성 공통). 빠른 확인용.",
    )

    # config의 값을 덮어쓰고 싶을 때만 사용한다. 지정하지 않으면 config 파일 값을 그대로 쓴다.
    parser.add_argument("--experiment-name")
    parser.add_argument("--chunk-size", type=int)
    parser.add_argument("--chunk-overlap", type=int)
    parser.add_argument("--search-strategy", choices=["similarity", "mmr", "bm25", "hybrid"])
    parser.add_argument("--k", type=int)
    parser.add_argument("--fetch-k", type=int)
    parser.add_argument("--lambda-mult", type=float)
    parser.add_argument("--context-k", type=int)
    parser.add_argument("--generation-model")
    parser.add_argument("--eval-model")
    parser.add_argument("--generation-case-limit", type=int)
    parser.add_argument("--collection-name")
    parser.add_argument("--rebuild-index", action=argparse.BooleanOptionalAction)
    parser.add_argument("--run-generation", action=argparse.BooleanOptionalAction)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir).resolve()

    # .env는 프로젝트 루트(my-ai-agent)에 있다.
    load_dotenv(base_dir.parent / ".env")

    config = RunConfig.from_file(args.config)
    overrides = {
        "experiment_name": args.experiment_name,
        "chunk_size": args.chunk_size,
        "chunk_overlap": args.chunk_overlap,
        "search_strategy": args.search_strategy,
        "k": args.k,
        "fetch_k": args.fetch_k,
        "lambda_mult": args.lambda_mult,
        "context_k": args.context_k,
        "generation_model": args.generation_model,
        "eval_model": args.eval_model,
        "generation_case_limit": args.generation_case_limit,
        "collection_name": args.collection_name,
        "rebuild_index": args.rebuild_index,
        "run_generation": args.run_generation,
    }
    config = config.with_overrides(overrides)

    if not args.dry_run and config.generation_case_limit is None and config.run_generation:
        print("경고: generation_case_limit이 없어 전체 문항으로 답변을 생성합니다. "
              "비용이 커질 수 있습니다.")

    experiment = run_experiment(config, base_dir, dry_run=args.dry_run, eval_limit=args.limit)

    if args.dry_run:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_root = Path(config.result_dir)
    result_root = result_root if result_root.is_absolute() else base_dir / config.result_dir
    output_dir = make_output_dir(result_root, config.experiment_name, timestamp)
    run_info = build_run_info(config.to_dict(), base_dir, timestamp)
    save_experiment(output_dir, experiment, run_info=run_info)

    print(f"\n결과 저장 완료: {output_dir}")


if __name__ == "__main__":
    main()
