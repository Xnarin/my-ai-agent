# company_rules_similarity

## 사용한 input

- 문서: `data/company_rules/*.md`
- 평가 데이터: `data/company_rules/eval_qa_50.json`
- 청킹: chunk_size=700, chunk_overlap=100
- 임베딩 모델: `gemini-embedding-2`
- 검색 전략: `similarity` (k=5, fetch_k=20, lambda_mult=0.5, weights=[0.5, 0.5])
- 생성 모델: `gemini-3.6-flash` / 평가 모델: `gemini-3.6-flash`
- 생성 평가 지표: ['citation_check', 'llm_judge']

## 검색 평가 결과

| 지표 | 값 |
|---|---|
| count | 50 |
| hit@1 | 0.980 |
| hit@3 | 1.000 |
| hit@5 | 1.000 |
| precision@5 | 0.648 |
| recall@3 | 0.895 |
| recall@5 | 0.935 |
| mrr | 0.990 |
| latency_ms | 4593.327 |

### 난이도별

| 난이도 | hit@1 | mrr | latency_ms |
|---|---|---|---|
| easy | 0.929 | 0.964 | 4593.3 |
| hard | 1.000 | 1.000 | 4593.3 |
| medium | 1.000 | 1.000 | 4593.3 |

## 답변 생성 평가 결과

### 인용 규칙 검사

| 지표 | 값 |
|---|---|
| count | 5 |
| valid_citation_rate | 1.000 |
| relevant_citation_rate | 1.000 |
| avg_latency_ms | 3970.701 |

### LLM-as-Judge

| 지표 | 값 |
|---|---|
| count | 5 |
| correctness | 10.000 |
| completeness | 10.000 |
| groundedness | 10.000 |
| citation_accuracy | 10.000 |
| average | 10.000 |
| avg_latency_ms | 4161.177 |

## 비용/시간 (trade-off)

- 검색 latency: 4593.3 ms/문항
- 답변 생성 latency: 3970.7 ms/문항
- Judge 평가 latency: 4161.2 ms/문항
