from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROJECT_DIR = Path(__file__).resolve().parent
ROOT_DIR = PROJECT_DIR.parent


def resolve_path(value: str, base_dir: Path = PROJECT_DIR) -> Path:
    path = Path(value)
    return path if path.is_absolute() else (base_dir / path).resolve()


def load_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path).resolve()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["config_path"] = str(config_path)
    config_dir = config_path.parent
    config["data"]["documents_dir"] = resolve_path(
        config["data"]["documents_dir"], config_dir
    )
    config["data"]["evaluation_path"] = resolve_path(
        config["data"]["evaluation_path"], config_dir
    )
    config["generation"]["prompt_path"] = resolve_path(
        config["generation"]["prompt_path"], config_dir
    )
    config["output_dir"] = resolve_path(config.get("output_dir", "outputs"))
    validate_config(config)
    return config


def validate_config(config: dict[str, Any]) -> None:
    required = {
        "name",
        "data",
        "chunking",
        "embedding",
        "retrieval",
        "generation",
        "evaluation",
    }
    missing = required - config.keys()
    if missing:
        raise ValueError(f"필수 설정이 없습니다: {', '.join(sorted(missing))}")

    chunking = config["chunking"]
    retrieval = config["retrieval"]
    if chunking["strategy"] != "recursive":
        raise ValueError("현재 수업 범위에서는 recursive 청킹만 지원합니다.")
    if chunking["chunk_size"] <= 0:
        raise ValueError("chunk_size는 양수여야 합니다.")
    if not 0 <= chunking["chunk_overlap"] < chunking["chunk_size"]:
        raise ValueError("chunk_overlap은 0 이상이고 chunk_size보다 작아야 합니다.")
    allowed = {"similarity", "mmr", "bm25", "hybrid"}
    unknown = set(retrieval["strategies"]) - allowed
    if unknown:
        raise ValueError(f"지원하지 않는 검색 전략: {', '.join(sorted(unknown))}")
    if retrieval["k"] <= 0 or retrieval["fetch_k"] < retrieval["k"]:
        raise ValueError("k는 양수이고 fetch_k는 k 이상이어야 합니다.")
    if not 0 <= retrieval["lambda_mult"] <= 1:
        raise ValueError("lambda_mult는 0과 1 사이여야 합니다.")
    weights = retrieval["weights"]
    if len(weights) != 2 or any(weight < 0 for weight in weights) or sum(weights) == 0:
        raise ValueError("Hybrid Search weights에는 0 이상의 값 두 개가 필요합니다.")

    generation = config["generation"]
    if not generation["prompt_path"].is_file():
        raise ValueError(
            f"프롬프트 파일을 찾을 수 없습니다: {generation['prompt_path']}"
        )
    if generation["context_k"] <= 0:
        raise ValueError("generation.context_k는 양수여야 합니다.")
    unavailable = set(generation["strategies"]) - set(retrieval["strategies"])
    if unavailable:
        raise ValueError(
            "생성 전략은 검색 전략에 포함되어야 합니다: "
            + ", ".join(sorted(unavailable))
        )

    allowed_metrics = {"faithfulness", "answer_relevancy", "answer_correctness"}
    unknown_metrics = set(config["evaluation"]["ragas_metrics"]) - allowed_metrics
    if unknown_metrics:
        raise ValueError(f"지원하지 않는 RAGAS 지표: {', '.join(sorted(unknown_metrics))}")
