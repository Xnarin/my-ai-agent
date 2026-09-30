# 업무 흐름에 필요한 State와 노드 함수를 정의합니다.
# 요청 해석, 업무 함수 호출, 승인·거절과 결과 안내를 연결합니다.
# LangGraph의 중단·재개로 사용자 승인을 처리합니다.
from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

import functions

load_dotenv()

MODEL_NAME = "gemini-3.6-flash"
llm = ChatGoogleGenerativeAI(model=MODEL_NAME)


class State(TypedDict):
    messages: Annotated[list, add_messages]
    intent: str
    from_account: str | None
    to_account: str | None
    amount: int | None
    result: str


class Request(BaseModel):
    intent: Literal["lookup", "transfer", "unknown"] = Field(
        description="lookup: 계좌 목록·잔액 조회, transfer: 계좌 간 이체, unknown: 그 외"
    )
    from_account: str | None = Field(default=None, description="출금 계좌 별명. 예: 생활비")
    to_account: str | None = Field(default=None, description="입금 계좌 별명. 예: 저축")
    amount: int | None = Field(
        default=None, description="이체 금액(원 단위 정수). 예: 10만 원 → 100000, -1만 원 → -10000"
    )


parser = llm.with_structured_output(Request)


def parse_request(state: State):
    """요청 해석: 업무 종류와 계좌·금액을 뽑는다."""
    request = parser.invoke([
        SystemMessage(content="은행 앱의 요청 해석기다. 대화를 참고해 마지막 사용자 요청을 해석한다. 말하지 않은 값은 비워 둔다."),
        *state["messages"],
    ])
    return request.model_dump()


def route_by_intent(state: State):
    """업무 확인: 업무 종류에 따라 다음 단계를 고른다."""
    return state["intent"]


def lookup(state: State):
    """계좌 조회"""
    return {"result": functions.lookup_accounts()}


def respond(state: State):
    """결과 안내: State를 보고 답변을 만든다."""
    if state["intent"] == "lookup":
        text = state["result"]
    elif state["intent"] == "transfer":
        # 5단계에서 이체 검사 → 승인 → 실행 흐름으로 바꾼다.
        text = f"이체 요청 확인: {state['from_account']} → {state['to_account']} {state['amount']}원 (승인 흐름은 준비 중)"
    else:
        text = "지금은 계좌 조회와 이체만 할 수 있어요."
    return {"messages": [AIMessage(content=text)]}


builder = StateGraph(State)
builder.add_node("parse_request", parse_request)
builder.add_node("lookup", lookup)
builder.add_node("respond", respond)

builder.add_edge(START, "parse_request")
builder.add_conditional_edges(
    "parse_request",
    route_by_intent,
    {"lookup": "lookup", "transfer": "respond", "unknown": "respond"},
)
builder.add_edge("lookup", "respond")
builder.add_edge("respond", END)

graph = builder.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    # 동작 확인: 조회·이체·그 외 요청이 어디로 가는지 본다.
    from data_store import prepare_data

    prepare_data()
    config = {"configurable": {"thread_id": "check"}}
    for text in ["내 계좌 목록과 잔액을 보여줘.", "생활비에서 저축으로 10만 원 옮겨줘.", "오늘 날씨 어때?"]:
        result = graph.invoke({"messages": [("user", text)]}, config)
        print(f"요청: {text}\n[{result['intent']}] {result['messages'][-1].content}\n")
