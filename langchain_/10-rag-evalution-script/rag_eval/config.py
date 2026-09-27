"""실험 조건을 정의하는 Config.

CONFIG_INPUT_OUTPUT_GUIDE.md에서 정리한 input 항목을 그대로 필드로 옮긴다.
config 파일(JSON)로 실험 조건을 분리해두면 코드를 수정하지 않고 여러 조건을
실행하고 비교할 수 있다.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

# 검색기 결과의 청크가 어떤 golden set 필드와 짝을 이루는지 정의한다.
# company_rules/eval_qa_50.json 형식을 기본값으로 삼는다.
DEFAULT_FIELD_MAP = {
    "id": "id",
    "question": "question",
    "expected_answer": "expected_answer",
    "source": "source",
    "page": "page",
    "difficulty": "difficulty",
}

VALID_SEARCH_STRATEGIES = {"similarity", "mmr", "bm25", "hybrid"}
VALID_GENERATION_METRICS = {"citation_check", "llm_judge", "ragas"}
VALID_RAGAS_METRICS = {"faithfulness", "answer_relevancy", "answer_correctness"}


@dataclass
class RunConfig:
    # --- 실험 식별 ---
    experiment_name: str = "experiment"

    # --- 문서와 평가 데이터 경로 (base_dir 기준 상대 경로 허용) ---
    document_glob: str = "data/company_rules/*.md"
    eval_data_path: str = "data/company_rules/eval_qa_50.json"
    eval_field_map: dict = field(default_factory=lambda: dict(DEFAULT_FIELD_MAP))

    # --- 청킹 설정 ---
    chunk_size: int = 500
    chunk_overlap: int = 50

    # --- 임베딩 / 벡터 스토어 ---
    embedding_model: str = "gemini-embedding-2"
    persist_dir: str = "./chroma_db"
    collection_name: str = "rag_eval_experiment"
    rebuild_index: bool = True

    # --- 검색 전략과 검색 설정 ---
    search_strategy: str = "similarity"  # similarity | mmr | bm25 | hybrid
    k: int = 5
    fetch_k: int = 20
    lambda_mult: float = 0.5
    weights: list = field(default_factory=lambda: [0.5, 0.5])

    # --- 답변 생성 ---
    context_k: int | None = None  # None이면 k와 동일
    prompt_path: str | None = None  # None이면 기본 프롬프트 사용
    generation_model: str = "gemini-3.6-flash"
    run_generation: bool = True
    generation_case_limit: int | None = 10  # None이면 전체 문항 사용 (비용 주의)

    # --- 답변 평가 ---
    eval_model: str | None = None  # None이면 generation_model과 동일
    generation_metrics: list = field(
        default_factory=lambda: ["citation_check", "llm_judge"]
    )
    # generation_metrics에 "ragas"가 포함될 때만 사용한다.
    ragas_metrics: list = field(
        default_factory=lambda: ["faithfulness", "answer_relevancy"]
    )

    # --- 429 재시도 설정 ---
    # 429(quota exhausted)가 반복되면 재시도 횟수를 넉넉히 늘린다. 시간이 조금 더
    # 걸릴 수 있다.
    retry_attempts: int = 12
    retry_initial_delay: float = 3.0
    retry_max_delay: float = 90.0

    # --- 결과 저장 ---
    result_dir: str = "10-rag-evalution-script/results"

    def __post_init__(self):
        if self.search_strategy not in VALID_SEARCH_STRATEGIES:
            raise ValueError(
                f"search_strategy는 {VALID_SEARCH_STRATEGIES} 중 하나여야 합니다: "
                f"{self.search_strategy!r}"
            )
        unknown_metrics = set(self.generation_metrics) - VALID_GENERATION_METRICS
        if unknown_metrics:
            raise ValueError(
                f"알 수 없는 generation_metrics: {unknown_metrics}. "
                f"사용 가능: {VALID_GENERATION_METRICS}"
            )
        unknown_ragas_metrics = set(self.ragas_metrics) - VALID_RAGAS_METRICS
        if unknown_ragas_metrics:
            raise ValueError(
                f"알 수 없는 ragas_metrics: {unknown_ragas_metrics}. "
                f"사용 가능: {VALID_RAGAS_METRICS}"
            )
        if self.context_k is None:
            self.context_k = self.k
        # 답변 생성은 검색 평가에서 이미 가져온 상위 k개 문서를 재사용하므로
        # context_k가 k보다 클 수 없다.
        self.context_k = min(self.context_k, self.k)
        if self.eval_model is None:
            self.eval_model = self.generation_model
        # dict/list 필드가 로드 과정에서 병합되지 않은 경우를 대비해 기본값을 보정한다.
        merged_field_map = dict(DEFAULT_FIELD_MAP)
        merged_field_map.update(self.eval_field_map or {})
        self.eval_field_map = merged_field_map

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_file(cls, path: str | Path) -> "RunConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict) -> "RunConfig":
        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"config에 알 수 없는 필드가 있습니다: {unknown}")
        return cls(**data)

    def with_overrides(self, overrides: dict) -> "RunConfig":
        """CLI 등에서 넘어온 값(None 제외)으로 새 Config를 만든다."""
        data = self.to_dict()
        for key, value in overrides.items():
            if value is not None:
                data[key] = value
        return RunConfig.from_dict(data)
