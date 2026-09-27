from __future__ import annotations

import argparse
import asyncio
import statistics
import sys

from dotenv import load_dotenv

from config import ROOT_DIR, load_config
from storage import read_jsonl, write_json, write_jsonl


async def evaluate(config: dict, limit: int | None) -> None:
    import instructor
    from google import genai
    from ragas.embeddings.base import embedding_factory
    from ragas.llms import InstructorLLM
    from ragas.metrics.collections import AnswerCorrectness, AnswerRelevancy, Faithfulness

    output_dir = config["output_dir"] / config["name"]
    rows = read_jsonl(output_dir / "generation.jsonl")
    if limit:
        strategies = list(dict.fromkeys(row["strategy"] for row in rows))
        rows = [
            row
            for strategy in strategies
            for row in [item for item in rows if item["strategy"] == strategy][:limit]
        ]

    google_client = genai.Client()
    instructor_client = instructor.from_genai(google_client, use_async=True)
    evaluator_llm = InstructorLLM(
        client=instructor_client,
        model=config["evaluation"]["model"],
        provider="google",
    )
    evaluator_embeddings = embedding_factory(
        "google",
        model=config["evaluation"]["embedding_model"],
        client=google_client,
    )

    async def embed_texts_individually(texts, **kwargs):
        return [
            await evaluator_embeddings.aembed_text(text, **kwargs) for text in texts
        ]

    evaluator_embeddings.aembed_texts = embed_texts_individually
    metric_names = config["evaluation"]["ragas_metrics"]
    metrics = {
        "faithfulness": (
            Faithfulness(llm=evaluator_llm),
            lambda row: {
                "user_input": row["question"],
                "response": row["response"],
                "retrieved_contexts": row["retrieved_contexts"],
            },
        ),
        "answer_relevancy": (
            AnswerRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings),
            lambda row: {"user_input": row["question"], "response": row["response"]},
        ),
        "answer_correctness": (
            AnswerCorrectness(llm=evaluator_llm, embeddings=evaluator_embeddings),
            lambda row: {
                "user_input": row["question"],
                "response": row["response"],
                "reference": row["target_answer"],
            },
        ),
    }
    scores_by_metric = {}
    for name in metric_names:
        metric, make_input = metrics[name]
        print(f"[RAGAS] {name} 평가 중 ({len(rows)}개 답변)")
        scores_by_metric[name] = await metric.abatch_score(
            [make_input(row) for row in rows]
        )
        print(f"[RAGAS] {name} 평가 완료 ({len(rows)}개 답변)")

    results = []
    for index, row in enumerate(rows):
        results.append(
            {
                **row,
                **{name: scores_by_metric[name][index].value for name in metric_names},
            }
        )
    summary = {}
    for strategy in dict.fromkeys(row["strategy"] for row in results):
        selected = [row for row in results if row["strategy"] == strategy]
        summary[strategy] = {"count": len(selected)}
        summary[strategy].update(
            {
                name: round(statistics.mean(row[name] for row in selected), 4)
                for name in metric_names
            }
        )
    write_jsonl(output_dir / "generation_evaluation.jsonl", results)
    write_json(output_dir / "generation_metrics.json", summary)
    print(f"[RAGAS] 전체 평가 완료: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="저장된 RAG 답변을 RAGAS로 평가")
    parser.add_argument("--config", required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    load_dotenv(ROOT_DIR / ".env")
    asyncio.run(evaluate(load_config(args.config), args.limit))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"오류: {error}", file=sys.stderr)
        raise SystemExit(1) from error
