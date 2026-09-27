"""평가 데이터셋(golden set) 로드.

company_rules/eval_qa_50.json과 public/public_paragraph_golden_set.json은
필드 이름이 다르다 (예: expected_answer vs target_answer, source vs
target_file_name). config의 eval_field_map으로 두 형식을 동일한 내부 표현으로
정규화한다.

정규화된 각 case는 다음 키를 가진다.
    id, question, expected_answer, relevant_sources(list[str]),
    target_page(int | None), difficulty

`id` 필드가 원본 데이터에 없으면(예: public golden set) 질문·정답 출처·페이지로
해시를 만들어 안정적인 ID를 부여한다. 문항 순서가 바뀌어도 같은 문항은 항상 같은
ID를 받으므로 서로 다른 실행 결과를 문항 단위로 비교할 수 있다.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _as_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def stable_case_id(question: str, sources: list[str], page: int | None) -> str:
    """질문, 정답 출처, 페이지로부터 결정적인(항상 같은 값을 내는) ID를 만든다."""
    key = "|".join([question, ",".join(sorted(sources)), str(page)])
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:10]
    return f"case_{digest}"


def load_eval_cases(eval_data_path: str | Path, field_map: dict) -> list[dict]:
    raw_cases = json.loads(Path(eval_data_path).read_text(encoding="utf-8"))
    if not isinstance(raw_cases, list):
        raise ValueError(f"평가 데이터는 JSON 배열이어야 합니다: {eval_data_path}")

    id_field = field_map.get("id", "id")
    question_field = field_map.get("question", "question")
    answer_field = field_map.get("expected_answer", "expected_answer")
    source_field = field_map.get("source", "source")
    page_field = field_map.get("page", "page")
    difficulty_field = field_map.get("difficulty", "difficulty")

    cases = []
    for index, raw in enumerate(raw_cases, start=1):
        if question_field not in raw:
            raise KeyError(
                f"평가 데이터 {index}번째 항목에 '{question_field}' 필드가 없습니다. "
                "eval_field_map 설정을 확인하세요."
            )
        if answer_field not in raw:
            raise KeyError(
                f"평가 데이터 {index}번째 항목에 '{answer_field}' 필드가 없습니다. "
                "eval_field_map 설정을 확인하세요."
            )

        question = raw[question_field]
        relevant_sources = _as_list(raw.get(source_field))
        target_page = raw.get(page_field)
        target_page = int(target_page) if target_page is not None else None

        case_id = raw.get(id_field)
        if case_id is None:
            case_id = stable_case_id(question, relevant_sources, target_page)

        cases.append({
            "id": case_id,
            "question": question,
            "expected_answer": raw[answer_field],
            "relevant_sources": relevant_sources,
            "target_page": target_page,
            "difficulty": raw.get(difficulty_field, "unknown"),
        })
    return cases
