from __future__ import annotations

import json
import hashlib
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


def load_documents(documents_dir: Path) -> list[Document]:
    paths = sorted(documents_dir.glob("*.pdf"))
    if not paths:
        raise FileNotFoundError(f"PDF 문서를 찾지 못했습니다: {documents_dir}")

    documents: list[Document] = []
    for path in paths:
        loaded = PyPDFLoader(path).load()
        for document in loaded:
            document.metadata["source"] = path.name
            document.metadata["page_no"] = document.metadata["page"] + 1
        documents.extend(loaded)
    return documents


def load_evaluation_cases(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    cases = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(cases, list):
        raise ValueError("평가셋의 최상위 값은 배열이어야 합니다.")
    required = {"question", "target_answer", "target_file_name", "target_page_no"}
    normalized = []
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"평가 문항 {index}는 객체여야 합니다.")
        missing = required - case.keys()
        if missing:
            raise ValueError(f"평가 문항 {index}의 필수 값이 없습니다: {', '.join(sorted(missing))}")
        item = dict(case)
        item.setdefault(
            "case_id",
            hashlib.sha256(
                f"{item['question']}\n{item['target_file_name']}\n{item['target_page_no']}".encode("utf-8")
            ).hexdigest()[:12],
        )
        normalized.append(item)
    return normalized[:limit] if limit is not None else normalized
