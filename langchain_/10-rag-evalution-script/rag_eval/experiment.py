"""하나의 Config로 검색 평가 → 답변 생성 → 답변 평가를 순서대로 실행한다.

각 단계는 이전 단계의 결과를 사용하며, 실패 원인을 구분할 수 있도록 검색 평가를
먼저 수행한다 (10-rag-evaluation.ipynb의 평가 순서와 동일). 답변 생성은 검색
평가 단계에서 이미 가져온 문서를 재사용하므로 같은 실험에서 검색을 두 번
실행하지 않는다.
"""

from __future__ import annotations

from pathlib import Path

from rag_eval import generation as gen
from rag_eval import metrics_generation as gen_metrics
from rag_eval import metrics_retrieval as ret_metrics
from rag_eval.config import RunConfig
from rag_eval.dataset import load_eval_cases
from rag_eval.indexing import build_vectorstore, chunk_documents, load_documents_by_file
from rag_eval.llm_setup import build_embeddings, build_llm
from rag_eval.retrieval import build_search_fn


def _resolve(base_dir: Path, path: str | None) -> str | None:
    if path is None:
        return None
    p = Path(path)
    return str(p if p.is_absolute() else base_dir / p)


def run_experiment(
    config: RunConfig,
    base_dir: Path,
    verbose: bool = True,
    dry_run: bool = False,
    eval_limit: int | None = None,
) -> dict:
    """dry_run=True이면 문서 로드·청킹과 문항 수 확인까지만 하고 임베딩 API를
    호출하지 않는다. eval_limit은 검색·생성 양쪽에 공통으로 적용되는 문항 수
    제한이며(빠른 확인용), config.generation_case_limit은 이후 생성 단계만 더
    줄이고 싶을 때 별도로 사용한다.
    """

    def log(message: str) -> None:
        if verbose:
            print(message)

    log(f"[{config.experiment_name}] 평가 데이터 로드 중...")
    eval_cases = load_eval_cases(
        _resolve(base_dir, config.eval_data_path), config.eval_field_map
    )
    if eval_limit is not None:
        eval_cases = eval_cases[:eval_limit]
    log(f"  문항 {len(eval_cases)}개")

    log(f"[{config.experiment_name}] 문서 로드 및 청킹 중... "
        f"(chunk_size={config.chunk_size}, chunk_overlap={config.chunk_overlap})")
    loaded_by_file = load_documents_by_file(config.document_glob, base_dir)
    chunks = chunk_documents(loaded_by_file, config.chunk_size, config.chunk_overlap)
    log(f"  문서 {len(loaded_by_file)}개 → 청크 {len(chunks)}개")

    if dry_run:
        log(f"[{config.experiment_name}] dry-run: 임베딩 API를 호출하지 않고 여기서 멈춥니다.")
        log(f"  검색 전략={config.search_strategy}  k={config.k}  fetch_k={config.fetch_k}  "
            f"lambda_mult={config.lambda_mult}  weights={config.weights}")
        log(f"  생성 모델={config.generation_model}  평가 모델={config.eval_model}  "
            f"generation_case_limit={config.generation_case_limit}")
        return {
            "dry_run": True,
            "config": config.to_dict(),
            "document_count": len(loaded_by_file),
            "chunk_count": len(chunks),
            "eval_case_count": len(eval_cases),
        }

    embeddings = build_embeddings(config)
    persist_dir = _resolve(base_dir, config.persist_dir)
    log(f"[{config.experiment_name}] 벡터 스토어 준비 중... "
        f"(rebuild_index={config.rebuild_index}, collection={config.collection_name})")
    vectorstore = build_vectorstore(
        chunks, embeddings, persist_dir, config.collection_name, config.rebuild_index
    )

    search_fn = build_search_fn(config, vectorstore, chunks)

    log(f"[{config.experiment_name}] 검색 평가 중... (전략={config.search_strategy}, k={config.k})")
    retrieval_result = ret_metrics.evaluate_retrieval(search_fn, eval_cases, config.k)
    retrieval_summary = ret_metrics.summarize_retrieval(retrieval_result, config.k)
    retrieval_by_difficulty = ret_metrics.summarize_by_difficulty(retrieval_result, config.k)
    log(f"  hit@1={retrieval_summary['hit@1']:.3f}  mrr={retrieval_summary['mrr']:.3f}  "
        f"latency={retrieval_summary['latency_ms']:.1f}ms/문항")

    experiment = {
        "config": config.to_dict(),
        "retrieval": {
            "rows": retrieval_result["rows"],
            "summary": retrieval_summary,
            "by_difficulty": retrieval_by_difficulty,
        },
    }

    if not config.run_generation:
        return experiment

    case_subset = eval_cases
    if config.generation_case_limit is not None:
        case_subset = eval_cases[: config.generation_case_limit]
    log(f"[{config.experiment_name}] 답변 생성 중... ({len(case_subset)}문항, "
        f"모델={config.generation_model}, 검색 재사용)")

    prompt_template = gen.load_prompt_template(_resolve(base_dir, config.prompt_path))
    generation_llm = build_llm(config, config.generation_model)
    generation_rows = gen.generate_answers(
        generation_llm,
        case_subset,
        retrieval_result["docs_by_case_id"],
        config.context_k,
        prompt_template,
    )

    generation: dict = {"rows": generation_rows}

    if "citation_check" in config.generation_metrics:
        generation["citation_check"] = gen_metrics.summarize_citation_check(generation_rows)
        log(f"  인용 유효율={generation['citation_check']['valid_citation_rate']:.3f}")

    if "llm_judge" in config.generation_metrics:
        log(f"[{config.experiment_name}] LLM-as-Judge 평가 중... (모델={config.eval_model})")
        judge_llm = build_llm(config, config.eval_model)
        judge_rows = gen_metrics.judge_answers(judge_llm, generation_rows)
        for row, score in zip(generation_rows, judge_rows):
            row["judge"] = score
        generation["llm_judge"] = gen_metrics.summarize_judge(judge_rows)
        log(f"  judge 평균={generation['llm_judge']['average']:.2f}/10")

    if "ragas" in config.generation_metrics:
        log(f"[{config.experiment_name}] RAGAS 평가 중... ({config.ragas_metrics})")
        try:
            ragas_rows = gen_metrics.run_ragas(
                generation_rows, config.embedding_model, config.eval_model, config.ragas_metrics
            )
            for row, score in zip(generation_rows, ragas_rows):
                row["ragas"] = score
            generation["ragas"] = gen_metrics.summarize_ragas(ragas_rows, config.ragas_metrics)
        except ImportError as exc:
            log(f"  RAGAS 평가를 건너뜁니다: {exc}")

    experiment["generation"] = generation
    return experiment
