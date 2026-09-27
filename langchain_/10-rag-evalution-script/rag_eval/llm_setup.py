"""임베딩 모델과 LLM을 준비한다.

429(quota exhausted) 에러가 반복될 때는 10번 자료에서 안내한 대로 재시도 설정을
추가하고 재시도 횟수를 넉넉히 늘린다. 여기서는 config의 retry_* 값으로 재시도
클라이언트를 만들어 embeddings와 llm에 공통으로 적용한다.
"""

from __future__ import annotations

from google import genai
from google.genai.types import HttpOptions, HttpRetryOptions
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from rag_eval.config import RunConfig


def build_retry_client(config: RunConfig) -> genai.Client:
    return genai.Client(
        http_options=HttpOptions(
            retry_options=HttpRetryOptions(
                attempts=config.retry_attempts,
                initial_delay=config.retry_initial_delay,
                max_delay=config.retry_max_delay,
                exp_base=2,
                jitter=1.0,
            )
        ),
    )


def build_embeddings(config: RunConfig) -> GoogleGenerativeAIEmbeddings:
    embeddings = GoogleGenerativeAIEmbeddings(model=config.embedding_model)
    embeddings.client = build_retry_client(config)
    return embeddings


def build_llm(config: RunConfig, model_name: str | None = None) -> ChatGoogleGenerativeAI:
    llm = ChatGoogleGenerativeAI(model=model_name or config.generation_model)
    # ChatGoogleGenerativeAI는 임베딩과 다른 내부 클라이언트를 사용할 수 있으므로
    # 429 재시도 클라이언트 적용은 best-effort로만 시도한다.
    try:
        llm.client = build_retry_client(config)
    except Exception:
        pass
    return llm
