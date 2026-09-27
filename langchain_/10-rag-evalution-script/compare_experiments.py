"""여러 config로 실험을 순서대로 실행하고 결과를 한 표로 비교한다.

같은 코드로 청크 크기, 검색 전략 등 조건만 다르게 바꿔가며 실행한 뒤 비교할 때
사용한다. 비교 대상 실험은 같은 평가 문항 집합(같은 golden set, 같은 --limit)을
사용해야 한다. 문항 집합이 다르면 비교 테이블을 만들기 전에 에러로 알린다.

사용 예시:
    python compare_experiments.py --configs configs/company_rules_similarity.json configs/company_rules_hybrid.json
    python compare_experiments.py --config-dir configs
    python compare_experiments.py --config-dir configs --limit 10
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from rag_eval.config import RunConfig
from rag_eval.experiment import run_experiment
from rag_eval.report import (
    assert_comparable,
    build_comparison_table,
    build_run_info,
    make_output_dir,
    render_comparison_md,
    save_comparison,
    save_experiment,
)

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_BASE_DIR = SCRIPT_DIR.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--configs", nargs="+", help="비교할 config JSON 파일 목록")
    group.add_argument("--config-dir", help="이 디렉터리의 모든 *.json config를 비교")
    parser.add_argument("--base-dir", default=str(DEFAULT_BASE_DIR))
    parser.add_argument(
        "--limit", type=int, default=None,
        help="golden set 앞쪽 N개 문항만 사용한다. 모든 config에 동일하게 적용된다.",
    )
    return parser.parse_args()


def resolve_config_paths(args: argparse.Namespace) -> list[Path]:
    if args.configs:
        return [Path(p) for p in args.configs]
    return sorted(Path(args.config_dir).glob("*.json"))


def main() -> None:
    args = parse_args()
    base_dir = Path(args.base_dir).resolve()
    load_dotenv(base_dir.parent / ".env")

    config_paths = resolve_config_paths(args)
    if not config_paths:
        raise SystemExit("실행할 config 파일을 찾지 못했습니다.")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    experiments = []
    for config_path in config_paths:
        config = RunConfig.from_file(config_path)
        print(f"\n=== {config.experiment_name} ({config_path}) ===")
        experiment = run_experiment(config, base_dir, eval_limit=args.limit)
        experiments.append(experiment)

        result_root = Path(config.result_dir)
        result_root = result_root if result_root.is_absolute() else base_dir / config.result_dir
        output_dir = make_output_dir(result_root, config.experiment_name, timestamp)
        run_info = build_run_info(config.to_dict(), base_dir, timestamp)
        save_experiment(output_dir, experiment, run_info=run_info)
        print(f"결과 저장: {output_dir}")

    try:
        assert_comparable(experiments)
    except ValueError as exc:
        raise SystemExit(f"비교할 수 없습니다: {exc}") from exc

    rows = build_comparison_table(experiments)
    comparison_dir = base_dir / "10-rag-evalution-script" / "results" / f"comparison_{timestamp}"
    save_comparison(comparison_dir, rows)

    print(f"\n비교 결과 저장: {comparison_dir}")
    print(render_comparison_md(rows))


if __name__ == "__main__":
    main()
