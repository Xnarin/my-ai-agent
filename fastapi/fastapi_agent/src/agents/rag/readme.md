### RAG Agent 준비

`.env`에 `GOOGLE_API_KEY`를 설정하고 프로젝트 디렉터리에서 문서를 적재한다.

```bash
uv run rag-ingest
```

`create_rag_agent()`는 저장된 Chroma의 검색기와 Gemini 모델을 사용한다. 검색할 청크 수는 `create_rag_agent(k=3)`처럼 지정하며 기본값은 4이다.

### 그래프 상태와 실행 흐름

```text
START → retrieve → generate → END
```

| 필드 | 용도 |
| --- | --- |
| `question` | 입력 질문 |
| `documents` | 검색된 문서 청크와 메타데이터 |
| `answer` | 최종 답변 |

`ainvoke()`는 `question`, `documents`, `answer`가 포함된 상태를 반환한다. 답변의 `[1]`, `[2]`는 검색된 문서 순서에 대응한다. Service는 `answer`를 꺼내 응답하고, 출처 정보가 필요하면 각 문서의 `metadata`를 사용한다.

### ainvoke로 최종 결과 받기

```python
import asyncio

from dotenv import load_dotenv

from agents.rag import create_rag_agent

load_dotenv()


async def main():
    agent = create_rag_agent()
    result = await agent.ainvoke({"question": "AI 산업의 주요 동향을 알려줘."})
    print(result["answer"])
    for document in result["documents"]:
        print(document.metadata)


asyncio.run(main())
```

체크포인터와 `thread_id` 없이 실행한다. 같은 Agent에 여러 질문을 전달해도 각 실행의 질문·검색 문서·답변은 독립적이다.

### astream으로 답변과 검색 결과 받기

`messages`는 모델이 생성하는 답변 조각을, `updates`는 노드별 상태 변경을 전달한다. `astream()`도 그래프를 실행하므로 한 요청에서는 원하는 응답 방식에 맞춰 `ainvoke()` 또는 `astream()`을 호출한다.

```python
import asyncio

from dotenv import load_dotenv

from agents.rag import create_rag_agent

load_dotenv()


async def main():
    agent = create_rag_agent()
    result = {"answer": "", "documents": []}

    async for mode, data in agent.astream(
        {"question": "AI 산업의 주요 동향을 알려줘."},
        stream_mode=["messages", "updates"],
    ):
        if mode == "messages":
            chunk, metadata = data
            if metadata.get("langgraph_node") == "generate" and chunk.text:
                print(chunk.text, end="", flush=True)
        elif mode == "updates":
            if "retrieve" in data:
                result["documents"] = data["retrieve"]["documents"]
            if "generate" in data:
                result["answer"] = data["generate"]["answer"]

    print()
    for document in result["documents"]:
        print(document.metadata)


asyncio.run(main())
```

FastAPI에서는 `messages`의 텍스트와 `updates`의 문서 메타데이터·최종 답변을 SSE 이벤트로 변환할 수 있다.
