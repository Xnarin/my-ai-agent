from __future__ import annotations

import argparse
import json
from pathlib import Path


OUTPUT_DIR = Path(__file__).resolve().parent / "outputs"
HEADERS = [
    "strategy",
    "file@1",
    "file@3",
    "file@5",
    "page@1",
    "page@3",
    "page@5",
    "MRR",
    "latency(ms)",
]


def format_metrics(metrics: dict) -> str:
    rows = [
        [
            strategy,
            f"{values['target_file_hit_1']:.4f}",
            f"{values['target_file_hit_3']:.4f}",
            f"{values['target_file_hit_5']:.4f}",
            f"{values['target_page_hit_1']:.4f}",
            f"{values['target_page_hit_3']:.4f}",
            f"{values['target_page_hit_5']:.4f}",
            f"{values['mrr']:.4f}",
            f"{values['avg_latency_ms']:.2f}",
        ]
        for strategy, values in metrics.items()
    ]
    widths = [
        max(len(HEADERS[index]), *(len(row[index]) for row in rows))
        for index in range(len(HEADERS))
    ]

    def format_row(row: list[str]) -> str:
        return "  ".join(
            value.ljust(widths[index]) if index == 0 else value.rjust(widths[index])
            for index, value in enumerate(row)
        )

    lines = [format_row(HEADERS), "  ".join("-" * width for width in widths)]
    lines.extend(format_row(row) for row in rows)
    return "\n".join(lines)


def find_metric_files(path: str | None) -> list[Path]:
    if path:
        target = Path(path).resolve()
        if target.is_dir():
            target = target / "retrieval_metrics.json"
        return [target]
    return sorted(OUTPUT_DIR.glob("*/retrieval_metrics.json"))


def main() -> None:
    parser = argparse.ArgumentParser(description="저장된 검색 평가 지표 출력")
    parser.add_argument("path", nargs="?", help="실험 디렉터리 또는 지표 JSON 경로")
    args = parser.parse_args()

    paths = find_metric_files(args.path)
    if not paths:
        raise SystemExit("출력할 retrieval_metrics.json이 없습니다.")

    for index, path in enumerate(paths):
        if not path.is_file():
            raise SystemExit(f"파일을 찾을 수 없습니다: {path}")
        if index:
            print()
        print(f"[{path.parent.name}]")
        metrics = json.loads(path.read_text(encoding="utf-8"))
        print(format_metrics(metrics))


if __name__ == "__main__":
    main()
