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
from langgraph.types import interrupt
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
    error: str
    decision: str
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
    """요청 해석: 업무 종류와 계좌·금액을 뽑고, 이전 요청의 불가 이유·결정·결과는 비운다."""
    request = parser.invoke([
        SystemMessage(content="은행 앱의 요청 해석기다. 대화를 참고해 마지막 사용자 요청을 해석한다. 말하지 않은 값은 비워 둔다."),
        *state["messages"],
    ])
    return {**request.model_dump(), "error": "", "decision": "", "result": ""}


def route_by_intent(state: State):
    """업무 확인: 업무 종류에 따라 다음 단계를 고른다."""
    return state["intent"]


def lookup(state: State):
    """계좌 조회"""
    return {"result": functions.lookup_accounts()}


def check(state: State):
    """이체 검사: 이체할 수 없으면 불가 이유를 적는다."""
    return {"error": functions.check_transfer(state["from_account"], state["to_account"], state["amount"])}


def route_by_check(state: State):
    """이체 가능?"""
    return "fail" if state["error"] else "ok"


def approval(state: State):
    """승인 요청 (중단): 사용자가 답할 때까지 멈춘다.
    재개되면 이 노드가 처음부터 다시 실행되므로, 여기서는 데이터를 바꾸지 않는다."""
    decision = interrupt({
        "question": "다음 이체를 승인하시겠습니까?",
        "detail": f"{state['from_account']} → {state['to_account']} {state['amount']:,}원",
    })
    return {"decision": decision["action"]}


def route_by_decision(state: State):
    """승인?"""
    return state["decision"]


def execute(state: State):
    """이체 실행 + 저장"""
    return {"result": functions.transfer(state["from_account"], state["to_account"], state["amount"])}


def respond(state: State):
    """결과 안내: 그 외 → 불가 → 거절 → 결과 순서로 확인해서 답한다."""
    if state["intent"] == "unknown":
        text = "지금은 계좌 조회와 이체만 할 수 있어요."
    elif state["error"]:
        text = state["error"]
    elif state["decision"] == "reject":
        text = "이체를 취소했어요. 잔액은 그대로예요."
    else:
        text = state["result"]
    return {"messages": [AIMessage(content=text)]}


builder = StateGraph(State)
builder.add_node("parse_request", parse_request)
builder.add_node("lookup", lookup)
builder.add_node("check", check)
builder.add_node("approval", approval)
builder.add_node("execute", execute)
builder.add_node("respond", respond)

builder.add_edge(START, "parse_request")
builder.add_conditional_edges(
    "parse_request",
    route_by_intent,
    {"lookup": "lookup", "transfer": "check", "unknown": "respond"},
)
builder.add_edge("lookup", "respond")
builder.add_conditional_edges("check", route_by_check, {"ok": "approval", "fail": "respond"})
builder.add_conditional_edges("approval", route_by_decision, {"approve": "execute", "reject": "respond"})
builder.add_edge("execute", "respond")
builder.add_edge("respond", END)

graph = builder.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    # 동작 확인: 승인하면 잔액이 바뀌고, 거절·불가면 그대로인지 본다. (시작과 끝에 작업용 데이터를 초기화함)
    from langgraph.types import Command

    from data_store import reset_data

    reset_data()
    config = {"configurable": {"thread_id": "check"}}
    for text, action in [
        ("생활비에서 저축으로 10만 원 옮겨줘.", "approve"),
        ("생활비에서 저축으로 5만 원 옮겨줘.", "reject"),
        ("생활비에서 저축으로 -1만 원 옮겨줘.", None),
    ]:
        result = graph.invoke({"messages": [("user", text)]}, config)
        assert ("__interrupt__" in result) == bool(action)  # 불가면 승인 요청 없이 끝나야 한다
        if action:
            result = graph.invoke(Command(resume={"action": action}), config)
        print(f"요청: {text} ({action or '승인 요청 없음'})\n답변: {result['messages'][-1].content}\n")
    assert "생활비: 1,331,800원" in functions.lookup_accounts()  # 승인한 10만 원만 반영
    reset_data()
    print("graph 확인 완료")
