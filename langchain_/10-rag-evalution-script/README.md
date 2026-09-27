# RAG 실험 평가 스크립트

`langchain_` 폴더의 08~10번 노트북(RAG 파이프라인, 검색 고도화, RAG 평가)에서
다룬 내용을 config 기반 파이썬 스크립트로 옮긴 것이다. 청킹 설정과 검색 전략을
비교한 뒤, 선택한 검색 결과로 답변을 생성하고 인용 규칙 검사·LLM-as-Judge·
RAGAS로 답변 품질을 평가한다.

평가는 다음 두 단계를 분리해서 수행한다.

- 검색 평가: 정답 근거가 있는 파일(과 페이지, 있는 경우)을 상위 k개 결과에서
  찾았는지 측정한다.
- 생성 평가: 검색 문맥으로 만든 답변의 근거성, 관련성, 정답성을 측정한다.

검색과 생성을 분리하면 검색 설정에 따른 변화와 LLM 답변 품질의 변화를 구분해서
해석할 수 있다. **생성 단계는 검색 평가 단계에서 이미 가져온 문서를 그대로
재사용하므로, 하나의 실행(`run_experiment.py` 한 번 실행) 안에서는 검색을
반복하지 않는다.** 참고 예제처럼 `retrieval.jsonl`을 저장했다가 별도의
`generate.py`로 다시 읽는 방식이 아니라, 같은 프로세스 안에서 메모리로 넘겨주는
방식으로 동일한 효과를 낸다.

### 프로젝트 구성

```text
10-rag-evalution-script/
├─ rag_eval/
│  ├─ config.py              # RunConfig: config JSON ↔ 실험 조건
│  ├─ dataset.py             # golden set 로드 + 필드 매핑 정규화 + 안정적 case_id
│  ├─ indexing.py            # 문서 로드(PDF/MD) → 청킹 → Chroma 벡터스토어
│  ├─ retrieval.py           # similarity/mmr/bm25/hybrid 검색기 빌더
│  ├─ metrics_retrieval.py   # Hit@k, Precision@k, Recall@k, MRR, Page Hit@k
│  ├─ generation.py          # 검색 문맥으로 답변 생성(인용 포함)
│  ├─ metrics_generation.py  # 인용 규칙 검사, LLM-as-Judge, RAGAS
│  ├─ experiment.py          # 검색 평가 → 답변 생성 → 답변 평가 오케스트레이션
│  ├─ report.py              # 결과 저장, run_info, 비교 테이블, 비교 가드
│  └─ llm_setup.py           # 임베딩/LLM 클라이언트 + 429 재시도 설정
├─ configs/
│  ├─ company_rules_similarity.json
│  ├─ company_rules_hybrid.json
│  └─ public_similarity.json
├─ results/                  # 실행 결과 저장 위치 (실행 시 자동 생성)
├─ run_experiment.py         # 단일 실험 실행 CLI
├─ compare_experiments.py    # 여러 실험 실행 + 비교 테이블 생성 CLI
├─ test_experiment.py        # API 호출 없는 단위 테스트
└─ CONFIG_INPUT_OUTPUT_GUIDE.md
```

문서(`data/company_rules`, `data/public`)와 Chroma 저장 위치(`chroma_db/`)는
이 폴더 안이 아니라 상위 `langchain_/` 폴더에 있다. 08~10번 노트북과 같은
데이터를 그대로 재사용하기 위해서다. config의 `document_glob`, `eval_data_path`,
`persist_dir` 같은 상대 경로는 **config 파일 위치가 아니라 `langchain_/` 폴더
(base-dir)를 기준으로 해석한다.**

### 실행 환경 준비

Python과 필요한 패키지(`langchain`, `langchain-chroma`, `langchain-google-genai`,
`chromadb`, `kiwipiepy`, `rank-bm25` 등)는 프로젝트 루트의 `.venv`에 이미
설치되어 있다고 가정한다. `my-ai-agent/.env`에 Gemini API 키를 설정한다.

```dotenv
GEMINI_API_KEY=발급받은_API_키
```

API 키가 포함된 `.env`는 저장소에 커밋하지 않는다. 이후 예제 디렉터리로
이동한다.

```powershell
cd langchain_/10-rag-evalution-script
```

이후 명령은 이 디렉터리에서 실행한다.

### 전체 실행 흐름

빠른 확인에는 `--dry-run`과 `--limit`을 사용한다. 전체 문항을 평가할 때는
두 옵션을 모두 제거한다.

```powershell
python run_experiment.py --config configs/company_rules_similarity.json --dry-run
python run_experiment.py --config configs/company_rules_similarity.json --limit 5
python run_experiment.py --config configs/company_rules_similarity.json
```

`--dry-run`은 문서 로드와 청킹까지 수행하여 문서 수, 청크 수, 평가 문항 수와
검색·생성 설정을 출력한다. 임베딩 API를 호출하거나 결과 파일을 저장하지
않으므로 본 실행 전에 경로와 설정을 확인하는 데 사용한다.

`--limit N`은 golden set의 앞쪽 N개 문항만 사용한다. 검색 평가와(생성이
켜져 있다면) 답변 생성에 공통으로 적용된다. 참고 예제와 달리 검색 전략은
config 하나당 하나만 실행하므로(아래 "검색 전략" 참고), `--limit`이 적용하는
검색 횟수는 항상 N회다.

답변 생성 자체를 더 줄이고 싶으면 config의 `generation_case_limit`(또는
`--generation-case-limit`)을 별도로 사용한다. `--limit 20`으로 검색은 20문항
모두 평가하면서, `generation_case_limit: 5`로 답변 생성과 LLM-as-Judge는
비용이 큰 5문항만 실행하는 식으로 조합할 수 있다.

### 검색 실험 실행

다음 명령은 청크 크기 700, Similarity Search 설정으로 검색을 평가하고 답변까지
생성한다.

```powershell
python run_experiment.py --config configs/company_rules_similarity.json
```

검색 평가만 필요하면 답변 생성을 끈다.

```powershell
python run_experiment.py --config configs/company_rules_similarity.json --no-run-generation
```

결과는 `results/company_rules_similarity_<타임스탬프>/`에 저장된다. 실행할
때마다 새 타임스탬프 디렉터리가 생기므로 이전 결과를 덮어쓰지 않는다.

### 청킹 설정과 검색 전략 비교

청크 크기나 검색 전략처럼 하나의 조건만 바꿔가며 비교하려면, config를
복사해 값만 바꾸고 `compare_experiments.py`로 한 번에 실행한다.

```powershell
python compare_experiments.py --configs configs/company_rules_similarity.json configs/company_rules_hybrid.json
python compare_experiments.py --config-dir configs
python compare_experiments.py --config-dir configs --limit 10
```

각 config는 독립적으로 실행되어 `results/<실험 이름>_<타임스탬프>/`에 저장되고,
전체 요약은 `results/comparison_<타임스탬프>/`에 `comparison.json` /
`comparison.md` / `comparison.csv`로 저장된다. 비교 대상 실험은 **같은 golden
set과 같은 `--limit`**을 사용해야 한다. 평가 문항 집합(`case_id`)이 다르면
비교 테이블을 만들기 전에 에러를 내고 멈춘다.

실험을 비교할 때는 한 번에 하나의 독립 변수만 바꾼다. 청크 크기를
비교한다면 문서, golden set, 검색 전략, `k`, 임베딩 모델을 동일하게
유지한다. Hybrid 가중치를 비교한다면 청킹 설정과 나머지 검색 조건을
동일하게 유지한다.

### 답변 생성과 프롬프트

답변 생성은 별도 명령이 아니라 `run_generation: true`(기본값)일 때
`run_experiment.py` 안에서 검색 평가 직후에 실행된다. 검색 평가에서 이미
가져온 상위 `context_k`개 문서를 그대로 사용하므로 검색을 다시 실행하지
않는다.

생성 프롬프트는 코드에 작성하지 않고 텍스트 파일로 관리할 수 있다. 사용할
파일은 config의 `prompt_path`에 지정한다(경로는 base-dir 기준). 지정하지
않으면 `rag_eval/generation.py`의 기본 프롬프트(검색 근거만 사용하고 출처를
citations에 표시하도록 지시)를 사용한다.

프롬프트 파일에는 검색 문맥이 들어갈 `{context}`와 질문이 들어갈
`{question}`이 모두 있어야 한다.

```text
제공된 참고 문서만 근거로 질문에 답하세요.

[참고 문서]
{context}

[질문]
{question}
```

### 답변 평가

`generation_metrics`에서 어떤 방식으로 답변을 평가할지 선택한다.

- `citation_check`: 규칙 기반 검사. 인용한 출처가 실제 검색 결과의
  부분집합인지(`valid_citation`), 정답 출처를 하나라도 인용했는지
  (`relevant_citation`)를 확인한다. LLM을 추가로 호출하지 않는다.
- `llm_judge`: 직접 정의한 LLM-as-Judge. 정확성·완전성·근거성·출처 정확성을
  1~10점으로 채점하고 평균과 판단 근거를 남긴다.
- `ragas`: RAGAS 라이브러리로 평가한다. `ragas_metrics`에서 세부 지표를
  고른다.
  - `faithfulness`: 답변의 주장들이 검색 문맥에 근거하는지
  - `answer_relevancy`: 답변이 질문과 관련 있는지
  - `answer_correctness`: 생성 답변과 golden set의 기준 답변이 의미상
    일치하는지

RAGAS는 기본 설치에 포함되어 있지 않다. `generation_metrics`에 `"ragas"`를
추가하기 전에 다음을 설치한다.

```powershell
pip install "ragas==0.4.3" "langchain-community==0.4.1" "instructor[google-genai]==1.15.4"
```

설치하지 않고 `"ragas"`를 켜면 설치 안내 메시지를 출력하고 해당 지표만
건너뛴다(다른 지표와 검색 평가는 정상적으로 저장된다).

하나의 지표만으로 최종 설정을 결정하지 않는다. Faithfulness가 높아도 검색
문맥 자체가 질문과 무관하면 정답성은 낮을 수 있다. 집계 점수와 함께
`generation_rows.json`의 질문, 문맥, 응답, 기준 답변을 함께 확인한다.

RAGAS와 LLM-as-Judge는 평가 LLM(및 RAGAS는 임베딩) API를 사용하므로 추가
호출 비용이 발생한다. 먼저 작은 `--limit`/`generation_case_limit`으로 전체
흐름을 확인한 다음 전체 평가를 실행한다.

### 검색 평가 지표

| 지표 | 의미 |
|---|---|
| `hit@1` / `hit@3` / `hit@k` | 상위 1·3·k개 검색 결과에 정답 파일이 하나라도 포함된 문항의 비율 |
| `precision@k` | 상위 k개 검색 결과 중 정답 파일에 속하는 청크의 비율 |
| `recall@3` / `recall@k` | 전체 정답 파일 중 상위 3·k개에서 찾은 파일의 비율 |
| `mrr` | 정답 파일이 처음 등장한 순위의 역수(RR)를 문항 평균한 값 |
| `page_hit@1` / `page_hit@3` / `page_hit@k` | 정답 파일의 **정답 페이지**가 상위 1·3·k개에 포함된 문항의 비율 |
| `page_eval_count` | golden set에 정답 페이지(`target_page`)가 있는 문항 수 |
| `latency_ms` | 질의 한 건의 평균 검색 시간(임베딩 API 호출 시간 포함, end-to-end) |

Hit·Recall·MRR·Page Hit는 0에서 1 사이이며 높을수록 좋다. `page_hit@k`는
golden set에 `target_page`가 있는 문항에서만 계산되며, 페이지 정보가 없는
golden set(예: `company_rules/eval_qa_50.json`)에서는 요약에 아예 나타나지
않는다. 파일 단위 적중은 같은 파일의 다른 페이지가 검색되어도 정답으로
인정하므로, `page_hit@k`가 더 엄격한 대리 지표다.

`page` 메타데이터는 `PyPDFLoader`가 0부터 매기므로, golden set의 사람이 보는
페이지 번호(`target_page_no`, 1부터 시작)와 비교할 때 1을 더해 맞춘다.

### 검색 전략

- Similarity Search는 질문과 의미적으로 가까운 청크를 벡터 유사도로 검색한다.
- MMR은 질문과의 관련성을 유지하면서 서로 중복되는 검색 결과를 줄인다.
- BM25는 Kiwi 형태소 분석 결과를 이용해 단어 기반으로 검색한다.
- Hybrid Search는 벡터 검색과 BM25 결과를 RRF(Reciprocal Rank Fusion)로
  결합한다.

한국어 조사와 활용형을 그대로 공백 단위로 나누면 BM25 검색 품질이 낮아질 수
있다. Kiwi로 명사·동사·수식언·어근·외국어·숫자 토큰을 추출해 BM25 입력으로
사용한다(`rag_eval/retrieval.py`의 `kiwi_tokenize`).

참고 예제와 달리 이 스크립트는 config 하나당 `search_strategy` **하나만**
실행한다. 네 전략을 모두 비교하려면 전략별로 config를 하나씩 만들고
`compare_experiments.py`로 함께 실행한다(`configs/company_rules_*.json`
참고).

### config 설정

```json
{
  "experiment_name": "company_rules_similarity",
  "document_glob": "data/company_rules/*.md",
  "eval_data_path": "data/company_rules/eval_qa_50.json",
  "chunk_size": 700,
  "chunk_overlap": 100,
  "embedding_model": "gemini-embedding-2",
  "persist_dir": "./chroma_db",
  "collection_name": "rag_eval_company_rules_similarity",
  "rebuild_index": true,
  "search_strategy": "similarity",
  "k": 5,
  "generation_model": "gemini-3.6-flash",
  "run_generation": true,
  "generation_case_limit": 5,
  "generation_metrics": ["citation_check", "llm_judge"]
}
```

| 필드 | 의미 |
|---|---|
| `experiment_name` | 결과 디렉터리 이름과 로그에 사용하는 실험 이름 |
| `document_glob` | 검색에 사용할 문서 경로 패턴(base-dir 기준). `.pdf`, `.md`, `.txt`를 자동으로 구분해 로드한다 |
| `eval_data_path` | golden set JSON 경로(base-dir 기준) |
| `eval_field_map` | golden set 필드 이름을 내부 이름(`question`, `expected_answer`, `source`, `page`, `difficulty`, `id`)에 매핑. 지정하지 않은 키는 기본값(`question`, `expected_answer`, `source`, `page`, `difficulty`, `id`)을 그대로 쓴다 |
| `chunk_size` / `chunk_overlap` | 문자 수 기준 청크 크기와 겹침 |
| `embedding_model` | 문서·질문 임베딩에 쓸 모델 |
| `persist_dir` / `collection_name` | Chroma 저장 위치와 컬렉션 이름 |
| `rebuild_index` | `true`면 기존 컬렉션을 지우고 다시 임베딩한다. `false`면 기존 컬렉션을 재사용하며, 저장된 청크 수가 현재 문서에서 만든 청크 수와 다르면 에러를 낸다(이전 실행이 429 등으로 중간에 실패해 컬렉션이 불완전하게 남는 것을 방지) |
| `search_strategy` | `similarity` / `mmr` / `bm25` / `hybrid` 중 하나 |
| `k` | 최종 검색 결과 수 |
| `fetch_k` | MMR과 Hybrid가 후보로 가져올 결과 수 |
| `lambda_mult` | MMR의 관련성-다양성 균형(1에 가까울수록 관련성 우선) |
| `weights` | Hybrid에서 [벡터 검색, BM25] 가중치 |
| `context_k` | 답변 생성에 전달할 상위 문서 수. `k`보다 클 수 없다(자동으로 `k`로 줄어든다) |
| `prompt_path` | 답변 생성 프롬프트 파일 경로(base-dir 기준). 없으면 기본 프롬프트 사용 |
| `generation_model` | 답변 생성 모델 |
| `run_generation` | `false`면 검색 평가만 수행하고 저장한다 |
| `generation_case_limit` | 답변 생성·평가에 사용할 문항 수 상한. `null`이면 전체 문항(비용 주의) |
| `eval_model` | LLM-as-Judge/RAGAS 평가에 쓸 모델. 없으면 `generation_model`과 동일 |
| `generation_metrics` | `citation_check` / `llm_judge` / `ragas` 중 선택 |
| `ragas_metrics` | `generation_metrics`에 `ragas`가 있을 때 계산할 세부 지표 |
| `retry_attempts` / `retry_initial_delay` / `retry_max_delay` | 429(quota exhausted) 재시도 설정 |
| `result_dir` | 결과 저장 루트 디렉터리(base-dir 기준) |

실험을 비교할 때는 한 번에 하나의 독립 변수만 변경한다.

### Golden set 형식

두 가지 형식을 `eval_field_map`으로 모두 지원한다.

`company_rules/eval_qa_50.json` (파일 단위 정답, 기본 필드 이름과 그대로
일치):

```json
[
  {
    "id": 1,
    "question": "연차는 며칠이야?",
    "expected_answer": "15일",
    "source": "인사규정.md",
    "difficulty": "easy"
  }
]
```

`public/public_paragraph_golden_set.json` (파일+페이지 단위 정답, config에서
`eval_field_map`으로 매핑):

```json
[
  {
    "question": "평가 질문",
    "target_answer": "기준 답변",
    "target_file_name": "근거 문서.pdf",
    "target_page_no": 3,
    "context_type": "paragraph"
  }
]
```

```json
"eval_field_map": {
  "expected_answer": "target_answer",
  "source": "target_file_name",
  "page": "target_page_no"
}
```

`source`는 문자열 하나 또는 문자열 목록을 모두 받는다(한 질문의 정답 근거가
여러 파일에 걸쳐 있는 경우). `id` 필드가 없으면 질문·정답 출처·페이지로부터
안정적인 ID(`case_<해시>`)를 만든다. golden set의 문항 순서가 달라져도 같은
문항은 항상 같은 ID를 받으므로, `compare_experiments.py`가 서로 다른 실행
결과를 문항 단위로 안전하게 비교할 수 있다.

### 결과 파일

각 실험은 `results/<실험 이름>_<타임스탬프>/`에 저장한다.

| 파일 | 내용 |
|---|---|
| `config.json` | 이 실행에 실제로 사용된 전체 설정(오버라이드 반영 후) |
| `retrieval_rows.json` | 문항별 검색 결과와 지표 |
| `retrieval_summary.json` | 검색 지표 요약(전체 + 난이도별) |
| `retrieval_misses.jsonl` | 정답을 다 찾지 못한 문항(`recall@k < 1`)만 모은 실패 분석용 파일. 한 줄에 문항 하나(JSONL) |
| `generation_rows.json` | 문항별 검색 문맥, 생성 답변, 인용, judge/ragas 점수 (`run_generation: true`일 때) |
| `generation_summary.json` | 인용 검사·LLM-as-Judge·RAGAS 요약 |
| `run_info.json` | 실행 시각, Python·패키지 버전, 문서/golden set 파일 해시(재현 확인용) |
| `summary.md` | 위 내용을 사람이 읽기 쉬운 표로 정리한 요약 |

`compare_experiments.py`는 위 파일들을 실험별로 저장한 뒤,
`results/comparison_<타임스탬프>/`에 `comparison.json` / `comparison.md` /
`comparison.csv`를 추가로 저장한다.

### 테스트

API를 호출하지 않는 단위 테스트는 이 디렉터리에서 실행한다.

```powershell
python -m pytest test_experiment.py -q
```

pytest가 없으면 먼저 설치한다(`pip install pytest`). 테스트는 config 로드와
검증 규칙, golden set의 안정적인 ID 생성, 검색 지표(Hit/Precision/Recall/MRR/
Page Hit) 계산, 검색 결과 재사용 구조, 서로 다른 평가 문항 집합에 대한 비교
차단을 확인한다. 테스트 통과 후 `--dry-run`, `--limit`을 준 실행, 전체 실행
순서로 범위를 넓힌다.

### 문제 해결

`'...' 패턴에 맞는 문서를 찾지 못했습니다`가 출력되면 config의
`document_glob`과 `--base-dir`(기본값: `langchain_/`)을 확인한다. 상대
경로는 config 파일 위치가 아니라 base-dir을 기준으로 해석한다.

`컬렉션 '...'이 없습니다` 또는 `저장된 청크 수가 ... 다릅니다` 에러가
나오면 `rebuild_index`를 `true`로 설정해 다시 색인한다. 후자는 이전 실행이
429 등으로 중간에 실패해 컬렉션이 불완전하게 남아 있다는 뜻이다.

API 인증 오류가 발생하면 `.env`의 `GEMINI_API_KEY`와 위치(`my-ai-agent/.env`)를
확인한다.

HTTP 429(RESOURCE_EXHAUSTED) 오류가 발생하면 API 할당량과 분당 요청 한도를
확인한다. 임베딩·생성·평가 요청에는 config의 `retry_attempts` /
`retry_initial_delay` / `retry_max_delay`만큼 지수 백오프와 무작위 지연을
적용한다(기본 12회, 최대 90초 대기). 재시도 후에도 오류가 계속되면
`retry_attempts`를 더 늘리거나 `--limit`을 줄여 실행하거나, 할당량이 갱신된
뒤 다시 실행한다. 시간이 조금 더 걸릴 수 있다.

RAGAS 관련 오류(`ImportError`)가 발생하면 위 "답변 평가" 절의 설치 명령을
실행했는지 확인한다. 설치 없이도 `citation_check`, `llm_judge`와 검색
평가는 정상적으로 동작한다.

`compare_experiments.py` 실행 중 `비교할 수 없습니다: 실험마다 평가 문항
집합이 다릅니다`가 출력되면, 비교 대상 config들이 같은 `eval_data_path`와
같은 `--limit`을 사용하는지 확인한다.
