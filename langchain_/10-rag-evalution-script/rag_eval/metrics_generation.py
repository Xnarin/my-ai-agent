"""생성된 답변을 평가하는 지표: 인용 규칙 검사, LLM-as-Judge, 선택적 RAGAS.

10-rag-evaluation.ipynb의 JudgeScore와 동일한 4개 항목(정확성/완전성/근거성/
출처 정확성)을 사용한다. RAGAS는 별도 설치(ragas, instructor 등)가 필요하므로
config.generation_metrics에 "ragas"가 포함된 경우에만 지연 임포트한다.
"""

from __future__ import annotations

import time

from pydantic import BaseModel, Field

JUDGE_METRIC_NAMES = ["correctness", "completeness", "groundedness", "citation_accuracy"]


class JudgeScore(BaseModel):
    correctness: int = Field(
        ge=1, le=10,
        description=(
            "기준 정답과 비교한 사실 정확성. 수치, 조건, 대상, 예외가 틀리면 감점한다. "
            "대부분 틀리면 1점, 핵심은 맞지만 일부 오류가 있으면 5점, 모든 핵심 사실이 "
            "정확하면 10점이다."
        ),
    )
    completeness: int = Field(
        ge=1, le=10,
        description=(
            "질문과 기준 정답이 요구하는 핵심 내용을 빠짐없이 포함한 정도. 핵심 내용을 "
            "거의 답하지 못하면 1점, 일부만 답하면 5점, 필요한 조건과 예외까지 모두 "
            "답하면 10점이다."
        ),
    )
    groundedness: int = Field(
        ge=1, le=10,
        description=(
            "모델 답변의 주장이 검색 문서로 뒷받침되는 정도. 주요 주장이 근거에 없거나 "
            "모순되면 1점, 일부만 근거가 있으면 5점, 모든 검증 가능한 주장이 검색 "
            "문서에 근거하면 10점이다."
        ),
    )
    citation_accuracy: int = Field(
        ge=1, le=10,
        description=(
            "인용한 파일이 실제 답변 내용을 지지하고 올바른 검색 출처인지 평가한다. "
            "인용이 없거나 잘못되면 1점, 일부 인용만 적절하면 5점, 필요한 인용이 모두 "
            "정확하면 10점이다."
        ),
    )
    reason: str = Field(description="항목별 판단 근거와 감점된 구체적인 이유")


def judge_answer(llm, item: dict) -> dict:
    judge_llm = llm.with_structured_output(JudgeScore)
    contexts = "\n\n".join(item["retrieved_contexts"])
    started = time.perf_counter()
    result = judge_llm.invoke(
        "각 항목을 설명된 기준에 따라 1~10점의 정수로 평가하세요. reason에는 항목별 "
        "판단과 감점 이유를 구체적으로 작성하세요.\n\n"
        f"질문: {item['question']}\n기준 정답: {item['expected_answer']}\n"
        f"모델 답변: {item['response']}\n인용: {item['citations']}\n검색 문서:\n{contexts}"
    )
    latency_ms = (time.perf_counter() - started) * 1000
    score = result.model_dump()
    score["average"] = round(
        sum(score[name] for name in JUDGE_METRIC_NAMES) / len(JUDGE_METRIC_NAMES), 2
    )
    score["latency_ms"] = latency_ms
    return score


def judge_answers(llm, generation_results: list[dict]) -> list[dict]:
    return [judge_answer(llm, item) for item in generation_results]


def summarize_citation_check(generation_results: list[dict]) -> dict:
    count = len(generation_results)
    if count == 0:
        return {"count": 0, "valid_citation_rate": 0.0, "relevant_citation_rate": 0.0}
    return {
        "count": count,
        "valid_citation_rate": sum(r["valid_citation"] for r in generation_results) / count,
        "relevant_citation_rate": sum(r["relevant_citation"] for r in generation_results) / count,
        "avg_latency_ms": sum(r["latency_ms"] for r in generation_results) / count,
    }


def summarize_judge(judge_results: list[dict]) -> dict:
    count = len(judge_results)
    if count == 0:
        return {"count": 0}
    summary = {"count": count}
    for name in JUDGE_METRIC_NAMES + ["average"]:
        summary[name] = sum(score[name] for score in judge_results) / count
    summary["avg_latency_ms"] = sum(score["latency_ms"] for score in judge_results) / count
    return summary


RAGAS_METRIC_INPUT_BUILDERS = {
    "faithfulness": lambda item: {
        "user_input": item["question"],
        "response": item["response"],
        "retrieved_contexts": item["retrieved_contexts"],
    },
    "answer_relevancy": lambda item: {
        "user_input": item["question"],
        "response": item["response"],
    },
    "answer_correctness": lambda item: {
        "user_input": item["question"],
        "response": item["response"],
        "reference": item["expected_answer"],
    },
}


def run_ragas(
    generation_results: list[dict],
    embedding_model: str,
    eval_model: str,
    metrics: list[str] = ("faithfulness", "answer_relevancy"),
) -> list[dict]:
    """RAGAS로 생성 답변을 평가한다. metrics는 다음 중에서 고른다.

    - faithfulness: 답변이 검색 문맥으로 뒷받침되는가
    - answer_relevancy: 답변이 질문과 관련되는가
    - answer_correctness: 답변이 기준 정답(reference)과 의미상 일치하는가

    ragas, instructor[google-genai] 설치가 필요하다.
        pip install "ragas==0.4.3" "langchain-community==0.4.1" "instructor[google-genai]==1.15.4"
    """
    try:
        import asyncio

        import instructor
        from google import genai
        from ragas.embeddings.base import embedding_factory
        from ragas.llms import InstructorLLM
        from ragas.metrics.collections import AnswerCorrectness, AnswerRelevancy, Faithfulness
    except ImportError as exc:
        raise ImportError(
            "RAGAS 평가에는 추가 패키지가 필요합니다: "
            'pip install "ragas==0.4.3" "langchain-community==0.4.1" '
            '"instructor[google-genai]==1.15.4"'
        ) from exc

    google_client = genai.Client()
    instructor_client = instructor.from_genai(google_client, use_async=True)
    evaluator_llm = InstructorLLM(client=instructor_client, model=eval_model, provider="google")
    evaluator_embeddings = embedding_factory(
        "google", model=embedding_model, client=google_client
    )

    async def embed_texts_individually(texts, **kwargs):
        return [await evaluator_embeddings.aembed_text(text, **kwargs) for text in texts]

    evaluator_embeddings.aembed_texts = embed_texts_individually

    metric_instances = {}
    if "faithfulness" in metrics:
        metric_instances["faithfulness"] = Faithfulness(llm=evaluator_llm)
    if "answer_relevancy" in metrics:
        metric_instances["answer_relevancy"] = AnswerRelevancy(
            llm=evaluator_llm, embeddings=evaluator_embeddings
        )
    if "answer_correctness" in metrics:
        metric_instances["answer_correctness"] = AnswerCorrectness(
            llm=evaluator_llm, embeddings=evaluator_embeddings
        )

    async def _run():
        scores_by_metric = {}
        for name, metric in metric_instances.items():
            build_input = RAGAS_METRIC_INPUT_BUILDERS[name]
            inputs = [build_input(item) for item in generation_results]
            scores_by_metric[name] = await metric.abatch_score(inputs)
        return [
            {name: scores_by_metric[name][i].value for name in metric_instances}
            for i in range(len(generation_results))
        ]

    return asyncio.run(_run())


def summarize_ragas(
    ragas_results: list[dict], metrics: list[str] = ("faithfulness", "answer_relevancy")
) -> dict:
    count = len(ragas_results)
    if count == 0:
        return {"count": 0}
    summary = {"count": count}
    summary.update({
        name: sum(r[name] for r in ragas_results) / count
        for name in metrics
        if all(name in r for r in ragas_results)
    })
    return summary
