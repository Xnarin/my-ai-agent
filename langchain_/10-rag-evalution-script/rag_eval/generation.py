"""검색 결과를 근거로 답변을 생성하고 인용 출처를 규칙으로 검사한다.

08-rag-pipeline.ipynb의 출처 표시 방식과 10-rag-evaluation.ipynb의
GroundedAnswer 구조화 출력을 따른다.
"""

from __future__ import annotations

import time
from pathlib import Path

from pydantic import BaseModel, Field

DEFAULT_PROMPT_TEMPLATE = (
    "너는 문서를 근거로 답변하는 어시스턴트야. 검색 근거만 사용해 답하고, "
    "답변에 사용한 문서 파일명을 citations에 작성해.\n"
    "검색 결과에 없는 내용은 답변에 포함하지 마.\n"
    "근거가 부족하면 '해당 정보를 찾을 수 없습니다'라고 답해.\n\n"
    "질문: {question}\n\n검색 근거:\n{context}"
)


class GroundedAnswer(BaseModel):
    answer: str = Field(description="검색 근거로 작성한 답변")
    citations: list[str] = Field(description="답변에 사용한 문서 파일명 목록")


def load_prompt_template(prompt_path: str | None) -> str:
    if not prompt_path:
        return DEFAULT_PROMPT_TEMPLATE
    text = Path(prompt_path).read_text(encoding="utf-8")
    if "{question}" not in text or "{context}" not in text:
        raise ValueError(
            f"prompt_path 파일에는 {{question}}, {{context}} 플레이스홀더가 필요합니다: {prompt_path}"
        )
    return text


def format_context(docs) -> list[str]:
    return [
        f"[출처: {doc.metadata.get('source', '?')}]\n{doc.page_content}"
        for doc in docs
    ]


def generate_answer(llm, case: dict, docs: list, context_k: int, prompt_template: str) -> dict:
    context_docs = docs[:context_k]
    retrieved_contexts = format_context(context_docs)
    retrieved_sources = {doc.metadata.get("source", "") for doc in context_docs}

    answer_llm = llm.with_structured_output(GroundedAnswer)
    started = time.perf_counter()
    result = answer_llm.invoke(
        prompt_template.format(
            question=case["question"], context="\n\n".join(retrieved_contexts)
        )
    )
    latency_ms = (time.perf_counter() - started) * 1000

    citations = set(result.citations)
    return {
        **case,
        "response": result.answer,
        "citations": result.citations,
        "retrieved_sources": sorted(retrieved_sources),
        "retrieved_contexts": retrieved_contexts,
        # 인용한 모든 출처가 실제 검색 결과의 부분집합이면 True.
        "valid_citation": bool(citations) and citations <= retrieved_sources,
        # 인용 출처와 정답 출처의 교집합이 있으면 True.
        "relevant_citation": bool(citations & set(case["relevant_sources"])),
        "latency_ms": latency_ms,
    }


def generate_answers(
    llm, cases: list[dict], docs_by_case_id: dict, context_k: int, prompt_template: str
) -> list[dict]:
    """검색 평가 단계에서 이미 가져온 문서를 재사용해 답변을 생성한다.

    같은 실험에서 검색을 두 번 실행하지 않도록 search_fn을 다시 호출하는 대신
    docs_by_case_id(=evaluate_retrieval의 결과)를 사용한다.
    """
    results = []
    for case in cases:
        docs = docs_by_case_id[case["id"]]
        results.append(generate_answer(llm, case, docs, context_k, prompt_template))
    return results
