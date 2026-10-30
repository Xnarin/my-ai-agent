### 도구형 챗봇

`create_chat_agent(checkpointer)`는 날씨·영화 조회 도구를 사용하는 Gemini Agent를 생성한다. 체크포인터는 호출하는 쪽에서 생성해 전달한다. 모델은 `gemini-3.6-flash`이며 `.env`에 `GOOGLE_API_KEY`를 설정한다.

| 도구 | 입력 | 반환 값 |
| --- | --- | --- |
| `search_weather` | 도시 이름 | 날씨·기온·습도 |
| `get_movie_list` | 목록 분류, 최대 개수 | 영화 ID·제목·개봉일 |
| `get_movie_detail` | 영화 ID | 줄거리·장르·러닝타임을 포함한 상세 정보 |

모든 도구는 고정된 더미 데이터를 반환한다. 영화는 가상 작품이며 실제 상영 정보와 관계없다. 도구 실행에는 외부 API나 별도 인증 키가 필요하지 않다.

### PostgreSQL 체크포인터 연결

FastAPI의 `lifespan`에서 체크포인터 연결을 열고 Agent를 생성한다. 앱이 실행되는 동안 연결을 유지하고 종료할 때 정리한다.

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.engine import make_url

from agents import create_chat_agent
from fastapi_agent.core.config import get_settings
from fastapi_agent.core.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    checkpoint_url = make_url(settings.database_url).set(drivername="postgresql")
    try:
        async with AsyncPostgresSaver.from_conn_string(
            checkpoint_url.render_as_string(hide_password=False)
        ) as checkpointer:
            await checkpointer.setup()
            app.state.chat_agent = create_chat_agent(checkpointer)
            yield
    finally:
        await engine.dispose()
```

`setup()`은 체크포인트 저장에 필요한 테이블을 준비한다. SQLAlchemy의 요청별 세션과 체크포인터 연결은 별도로 관리한다.

### 비동기 실행

Service는 채팅방 소유권을 확인한 뒤 저장된 채팅방 ID로 `thread_id`를 결정한다. 클라이언트가 보낸 임의의 `thread_id`를 그대로 사용하지 않는다.

```python
config = {"configurable": {"thread_id": f"chat:{room.id}"}}

result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "현재 상영 중인 영화 5개 알려줘."}]},
    config=config,
)
answer = result["messages"][-1].text

result = await agent.ainvoke(
    {"messages": [{"role": "user", "content": "그중 첫 번째 영화의 줄거리와 러닝타임은?"}]},
    config=config,
)
answer = result["messages"][-1].text
```

같은 채팅방에서는 동일한 `thread_id`를 사용하고 새 사용자 메시지만 전달한다. Agent는 저장된 메시지와 도구 결과를 읽어 후속 질문에 답한다. 다른 채팅방에는 별도의 `thread_id`를 사용한다.

Agent의 메시지에는 사용자 질문과 최종 답변뿐 아니라 도구 호출과 도구 결과도 포함된다. 화면용 대화 기록은 Service와 Repository에서 별도로 저장한다.
