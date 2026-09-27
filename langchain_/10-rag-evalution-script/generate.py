from __future__ import annotations

import argparse
import sys
import time

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from config import ROOT_DIR, load_config
from generation import build_context, load_prompt
from storage import read_jsonl, write_json, write_jsonl


class GroundedAnswer(BaseModel):
    answer: str = Field(description="검색 근거로 작성한 답변")
    citations: list[str] = Field(description="답변에 사용한 PDF 파일명")


def main() -> None:
    parser = argparse.ArgumentParser(description="저장된 검색 결과로 RAG 답변 생성")
    parser.add_argument("--config", required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()

    load_dotenv(ROOT_DIR / ".env")
    config = load_config(args.config)
    output_dir = config["output_dir"] / config["name"]
    retrieval_rows = read_jsonl(output_dir / "retrieval.jsonl")
    selected_strategies = config["generation"]["strategies"]
    selected = [
        row for row in retrieval_rows if row["strategy"] in selected_strategies
    ]
    if args.limit:
        selected = [
            row
            for strategy in selected_strategies
            for row in [item for item in selected if item["strategy"] == strategy][
                : args.limit
            ]
        ]

    llm = ChatGoogleGenerativeAI(
        model=config["generation"]["model"],
    ).with_structured_output(GroundedAnswer)
    prompt_template = load_prompt(config["generation"]["prompt_path"])

    results = []
    for index, row in enumerate(selected, start=1):
        context = build_context(
            row["documents"], config["generation"]["context_k"]
        )
        prompt = prompt_template.format(
            question=row["question"], context=context
        )
        started = time.perf_counter()
        answer = llm.invoke(prompt)
        latency_ms = round((time.perf_counter() - started) * 1000, 2)
        results.append(
            {
                "experiment": config["name"],
                "strategy": row["strategy"],
                "query_id": row["query_id"],
                "question": row["question"],
                "target_answer": row["target_answer"],
                "target_file_name": row["target_file_name"],
                "target_page_no": row["target_page_no"],
                "retrieved_contexts": [
                    document["content"]
                    for document in row["documents"][: config["generation"]["context_k"]]
                ],
                "response": answer.answer,
                "citations": answer.citations,
                "generation_latency_ms": latency_ms,
            }
        )
        status = "생성 완료" if index == len(selected) else "생성 중"
        print(f"[{row['strategy']}] {index}/{len(selected)}개 답변 {status}")

    write_jsonl(output_dir / "generation.jsonl", results)
    write_json(
        output_dir / "generation_summary.json",
        {
            "count": len(results),
            "strategies": selected_strategies,
            "model": config["generation"]["model"],
            "prompt_path": config["generation"]["prompt_path"],
        },
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"오류: {error}", file=sys.stderr)
        raise SystemExit(1) from error
