from __future__ import annotations

from pathlib import Path
from typing import Any


def load_prompt(path: Path) -> str:
    template = path.read_text(encoding="utf-8")
    missing = [field for field in ("{context}", "{question}") if field not in template]
    if missing:
        raise ValueError(
            f"프롬프트에 필수 변수가 없습니다: {', '.join(missing)} ({path})"
        )
    return template


def build_context(documents: list[dict[str, Any]], context_k: int) -> str:
    blocks: list[str] = []
    for document in documents[:context_k]:
        blocks.append(
            f"[출처: {document['source']}, 페이지: {document['page_no']}]\n"
            f"{document['content']}"
        )
    return "\n\n---\n\n".join(blocks)
