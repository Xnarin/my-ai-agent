from __future__ import annotations

import json
import hashlib
import platform
from importlib.metadata import PackageNotFoundError, version
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


def json_default(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"JSON으로 변환할 수 없는 값입니다: {type(value)}")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=json_default),
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, default=json_default) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def save_run_config(path: Path, config: dict[str, Any]) -> None:
    tracked_packages = [
        "chromadb",
        "langchain",
        "langchain-chroma",
        "langchain-google-genai",
        "ragas",
    ]
    package_versions = {}
    for package in tracked_packages:
        try:
            package_versions[package] = version(package)
        except PackageNotFoundError:
            package_versions[package] = None

    evaluation_path = config["data"]["evaluation_path"]
    document_paths = sorted(config["data"]["documents_dir"].glob("*.pdf"))
    write_json(
        path,
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "python_version": platform.python_version(),
            "package_versions": package_versions,
            "evaluation_sha256": file_sha256(evaluation_path),
            "documents": [
                {"name": document.name, "sha256": file_sha256(document)}
                for document in document_paths
            ],
            "config": config,
        },
    )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
