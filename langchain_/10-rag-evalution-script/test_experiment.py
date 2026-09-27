"""API를 호출하지 않는 단위 테스트.

config 로드, golden set 정규화와 안정적인 case_id, 검색 지표 계산, 서로 다른
평가 문항 집합에 대한 비교 차단을 검증한다. 실행:

    python -m pytest test_experiment.py -q

임베딩·LLM API를 호출하지 않으므로 빠르고 반복 실행에 부담이 없다. 이 테스트를
통과한 뒤 `--dry-run`, `--limit`을 준 실제 실행, 전체 실행 순서로 범위를 넓힌다.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from langchain_core.documents import Document

from rag_eval.config import RunConfig
from rag_eval.dataset import load_eval_cases, stable_case_id
from rag_eval.metrics_retrieval import (
    evaluate_retrieval,
    hit_at_k,
    page_hit_at_k,
    precision_at_k,
    reciprocal_rank,
    recall_at_k,
    summarize_retrieval,
)
from rag_eval.report import assert_comparable

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIGS_DIR = SCRIPT_DIR / "configs"


# --- config ---

def test_config_loads_from_example_files():
    for config_path in CONFIGS_DIR.glob("*.json"):
        config = RunConfig.from_file(config_path)
        assert config.experiment_name
        assert config.search_strategy in {"similarity", "mmr", "bm25", "hybrid"}
        # context_k는 항상 채워지고 k를 넘지 않는다.
        assert config.context_k is not None
        assert config.context_k <= config.k
        # eval_model이 비어 있으면 generation_model로 채워진다.
        assert config.eval_model


def test_config_rejects_unknown_search_strategy():
    with pytest.raises(ValueError):
        RunConfig(search_strategy="not-a-strategy")


def test_config_rejects_unknown_generation_metric():
    with pytest.raises(ValueError):
        RunConfig(generation_metrics=["not-a-metric"])


def test_config_rejects_unknown_field():
    with pytest.raises(ValueError):
        RunConfig.from_dict({"totally_unknown_field": 1})


def test_config_context_k_is_clamped_to_k():
    config = RunConfig(k=3, context_k=10)
    assert config.context_k == 3


# --- dataset ---

def test_stable_case_id_is_deterministic():
    id_a = stable_case_id("질문", ["a.md"], 3)
    id_b = stable_case_id("질문", ["a.md"], 3)
    assert id_a == id_b


def test_stable_case_id_changes_with_content():
    id_a = stable_case_id("질문 A", ["a.md"], 3)
    id_b = stable_case_id("질문 B", ["a.md"], 3)
    assert id_a != id_b


def test_load_eval_cases_with_explicit_id(tmp_path):
    data = [
        {"id": 1, "question": "연차는?", "expected_answer": "15일", "source": "인사규정.md", "difficulty": "easy"},
    ]
    path = tmp_path / "eval.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    cases = load_eval_cases(path, {"id": "id", "question": "question", "expected_answer": "expected_answer", "source": "source", "page": "page", "difficulty": "difficulty"})
    assert cases[0]["id"] == 1
    assert cases[0]["relevant_sources"] == ["인사규정.md"]
    assert cases[0]["target_page"] is None


def test_load_eval_cases_without_id_generates_stable_id(tmp_path):
    data = [
        {"question": "Q", "target_answer": "A", "target_file_name": "doc.pdf", "target_page_no": 3},
    ]
    path = tmp_path / "golden.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    field_map = {"expected_answer": "target_answer", "source": "target_file_name", "page": "target_page_no"}
    cases = load_eval_cases(path, {**{"id": "id", "question": "question", "difficulty": "difficulty"}, **field_map})

    assert cases[0]["id"] == stable_case_id("Q", ["doc.pdf"], 3)
    assert cases[0]["target_page"] == 3
    assert cases[0]["relevant_sources"] == ["doc.pdf"]


def test_load_eval_cases_missing_required_field_raises(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text(json.dumps([{"question": "Q"}], ensure_ascii=False), encoding="utf-8")
    with pytest.raises(KeyError):
        load_eval_cases(path, {"question": "question", "expected_answer": "expected_answer"})


# --- 검색 지표 ---

def test_hit_precision_recall_mrr():
    ranked = ["보안규정.md", "개인정보보호규정.md", "보안규정.md"]
    relevant = ["보안규정.md"]

    assert hit_at_k(ranked, relevant, 1) == 1
    assert hit_at_k(["개인정보보호규정.md"], relevant, 1) == 0
    assert precision_at_k(ranked, relevant, 3) == pytest.approx(2 / 3)
    assert recall_at_k(ranked, relevant, 3) == 1.0
    assert reciprocal_rank(ranked, relevant) == 1.0
    assert reciprocal_rank(["개인정보보호규정.md", "보안규정.md"], relevant) == 0.5


def test_page_hit_at_k_matches_source_and_page():
    ranked_sources = ["doc.pdf", "doc.pdf", "other.pdf"]
    ranked_pages = [0, 2, 2]  # PyPDFLoader는 0-indexed
    relevant = ["doc.pdf"]

    # 정답 페이지(사람 기준 3페이지 = index 2)가 2번째 결과에 있다.
    assert page_hit_at_k(ranked_sources, ranked_pages, relevant, target_page=3, k=1) == 0
    assert page_hit_at_k(ranked_sources, ranked_pages, relevant, target_page=3, k=2) == 1
    # target_page가 없으면 집계에서 제외하도록 None을 반환한다.
    assert page_hit_at_k(ranked_sources, ranked_pages, relevant, target_page=None, k=2) is None


def _fake_search_fn(docs_by_question: dict):
    def search(question: str):
        return docs_by_question[question]
    return search


def test_evaluate_retrieval_returns_docs_for_reuse_and_page_metrics():
    doc_hit = Document(page_content="content", metadata={"source": "doc.pdf", "page": 2})
    doc_miss = Document(page_content="content", metadata={"source": "other.pdf", "page": 0})

    cases = [
        {"id": "c1", "question": "q1", "expected_answer": "a", "relevant_sources": ["doc.pdf"], "target_page": 3, "difficulty": "easy"},
        {"id": "c2", "question": "q2", "expected_answer": "a", "relevant_sources": ["doc.pdf"], "target_page": None, "difficulty": "easy"},
    ]
    search_fn = _fake_search_fn({"q1": [doc_hit, doc_miss], "q2": [doc_miss]})

    result = evaluate_retrieval(search_fn, cases, k=5)
    assert set(result["docs_by_case_id"].keys()) == {"c1", "c2"}
    assert result["docs_by_case_id"]["c1"] == [doc_hit, doc_miss]

    summary = summarize_retrieval(result, k=5)
    # c1은 page_hit=1, c2는 target_page가 없어 집계에서 제외되므로 평균은 1.0이다.
    assert summary["page_eval_count"] == 1
    assert summary["page_hit@5"] == 1.0


# --- 비교 가드 ---

def _fake_experiment(name: str, ids: list) -> dict:
    return {
        "config": {"experiment_name": name},
        "retrieval": {"rows": [{"id": i} for i in ids]},
    }


def test_assert_comparable_allows_same_case_ids():
    experiments = [_fake_experiment("a", [1, 2, 3]), _fake_experiment("b", [1, 2, 3])]
    assert_comparable(experiments)  # 예외가 없어야 한다.


def test_assert_comparable_blocks_mismatched_case_ids():
    experiments = [_fake_experiment("a", [1, 2, 3]), _fake_experiment("b", [1, 2])]
    with pytest.raises(ValueError):
        assert_comparable(experiments)
