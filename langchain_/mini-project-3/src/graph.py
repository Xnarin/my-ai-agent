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
    card_name: str | None
    error: str
    decision: str
    result: str


class Request(BaseModel):
    intent: Literal["lookup", "card_lookup", "history", "transfer", "card_lost", "unknown"] = Field(
        description=(
            "lookup: 계좌 목록·잔액 조회, card_lookup: 카드 목록·상태 조회, "
            "history: 앞서 한 이체·카드 분실 정지가 처리됐는지 확인 (예: 아까 이체가 됐어?), "
            "transfer: 계좌 간 이체, card_lost: 카드 분실 정지, unknown: 그 외"
        )
    )
    from_account: str | None = Field(default=None, description="출금 계좌 별명. 예: 생활비")
    to_account: str | None = Field(default=None, description="입금 계좌 별명. 예: 저축")
    amount: int | None = Field(
        default=None, description="이체 금액(원 단위 정수). 예: 10만 원 → 100000, -1만 원 → -10000"
    )
    card_name: str | None = Field(default=None, description="카드 이름. 예: 생활비 카드")


parser = llm.with_structured_output(Request)


def parse_request(state: State):
    """요청 해석: 업무 종류와 계좌·금액·카드를 뽑고, 이전 요청의 불가 이유·결정·결과는 비운다."""
    request = parser.invoke([
        SystemMessage(content=(
            "은행 앱의 요청 해석기다. 대화를 참고해 마지막 사용자 요청을 해석한다. 말하지 않은 값은 비워 둔다. "
            "앞에서 되물은 질문에 답한 것이면 앞 요청과 합쳐서 해석한다."
        )),
        *state["messages"],
    ])
    return {**request.model_dump(), "error": "", "decision": "", "result": ""}


def route_by_intent(state: State):
    """업무 확인: 업무 종류에 따라 다음 단계를 고른다."""
    return state["intent"]


def lookup(state: State):
    """조회: 계좌, 카드 또는 처리 기록"""
    if state["intent"] == "card_lookup":
        return {"result": functions.lookup_cards()}
    if state["intent"] == "history":
        # 사용자가 가리키는 요청은 대화 맥락으로 찾아야 해서, 처리 기록을 근거로 LLM이 답한다.
        answer = llm.invoke([
            SystemMessage(content=(
                f"처리 기록:\n{functions.lookup_requests()}\n\n"
                "처리 기록만 근거로, 사용자가 가리키는 요청이 완료·거절·실패 중 무엇인지와 처리 내용을 한두 문장으로 답한다."
            )),
            *state["messages"],
        ])
        return {"result": answer.text}
    return {"result": functions.lookup_accounts()}


def check(state: State):
    """변경 검사: 할 수 없으면 불가 이유나 되물을 질문을 적는다."""
    if state["intent"] == "card_lost":
        return {"error": functions.check_card_lost(state["card_name"])}
    return {"error": functions.check_transfer(state["from_account"], state["to_account"], state["amount"])}


def route_by_check(state: State):
    """변경 가능?"""
    return "fail" if state["error"] else "ok"


def approval(state: State):
    """승인 요청 (중단): 사용자가 답할 때까지 멈춘다.
    재개되면 이 노드가 처음부터 다시 실행되므로, 여기서는 데이터를 바꾸지 않는다."""
    if state["intent"] == "card_lost":
        question, detail = "다음 카드를 분실 정지하시겠습니까?", state["card_name"]
    else:
        question = "다음 이체를 승인하시겠습니까?"
        detail = f"{state['from_account']} → {state['to_account']} {state['amount']:,}원"
    decision = interrupt({"question": question, "detail": detail})
    return {"decision": decision["action"]}


def route_by_decision(state: State):
    """승인?"""
    return state["decision"]


def execute(state: State):
    """변경 실행 + 저장"""
    if state["intent"] == "card_lost":
        return {"result": functions.report_card_lost(state["card_name"])}
    return {"result": functions.transfer(state["from_account"], state["to_account"], state["amount"])}


def record(state: State):
    """처리 기록: 변경 요청의 결과(완료·거절·실패)를 requests에 남긴다. 되물은 경우도 진행 안 됨(실패)으로 남는다."""
    if state["intent"] == "card_lost":
        target = {"card_name": state["card_name"]}
    else:
        target = {"from_account": state["from_account"], "to_account": state["to_account"], "amount": state["amount"]}
    if state["error"]:
        status, result = "failed", state["error"]
    elif state["decision"] == "reject":
        status, result = "rejected", "사용자가 거절함"
    else:
        status, result = "completed", state["result"]
    # ponytail: 변경 저장과 기록 저장이 따로라 그 사이에 꺼지면 기록만 빠진다. 필요하면 변경 함수 안에서 함께 저장.
    functions.record_request(state["intent"], target, status, result)
    return {}


def respond(state: State):
    """결과 안내: 그 외 → 불가 → 거절 → 결과 순서로 확인해서 답한다."""
    if state["intent"] == "unknown":
        text = "지금은 계좌·카드 조회, 이체, 카드 분실 정지, 처리 결과 확인만 할 수 있어요."
    elif state["error"]:
        text = state["error"]
    elif state["decision"] == "reject":
        text = "요청을 취소했어요. 바뀐 것은 없어요."
    else:
        text = state["result"]
    return {"messages": [AIMessage(content=text)]}


builder = StateGraph(State)
builder.add_node("parse_request", parse_request)
builder.add_node("lookup", lookup)
builder.add_node("check", check)
builder.add_node("approval", approval)
builder.add_node("execute", execute)
builder.add_node("record", record)
builder.add_node("respond", respond)

builder.add_edge(START, "parse_request")
builder.add_conditional_edges(
    "parse_request",
    route_by_intent,
    {
        "lookup": "lookup",
        "card_lookup": "lookup",
        "history": "lookup",
        "transfer": "check",
        "card_lost": "check",
        "unknown": "respond",
    },
)
builder.add_edge("lookup", "respond")
builder.add_conditional_edges("check", route_by_check, {"ok": "approval", "fail": "record"})
builder.add_conditional_edges("approval", route_by_decision, {"approve": "execute", "reject": "record"})
builder.add_edge("execute", "record")
builder.add_edge("record", "respond")
builder.add_edge("respond", END)

graph = builder.compile(checkpointer=MemorySaver())


if __name__ == "__main__":
    # 동작 확인: 빠진 정보를 되묻고 답을 반영하는지, 승인하면 바뀌고 거절·불가면 그대로인지,
    # 카드를 분실 정지하면 상태가 바뀌고 이미 정지된 카드는 승인 요청 없이 안내하는지,
    # 변경 요청마다 처리 기록이 남고 "아까 이체가 됐어?"에 기록으로 답하는지 본다.
    # (시작과 끝에 작업용 데이터를 초기화함)
    from langgraph.types import Command

    from data_store import read_data, reset_data

    reset_data()
    config = {"configurable": {"thread_id": "check"}}
    for text, action in [
        ("저축으로 10만 원 옮겨줘.", None),
        ("생활비에서", "approve"),
        ("생활비에서 저축으로 5만 원 옮겨줘.", "reject"),
        ("생활비에서 저축으로 -1만 원 옮겨줘.", None),
        ("생활비 카드 잃어버렸어. 정지해줘.", "approve"),
        ("내 카드 목록과 상태를 보여줘.", None),
        ("생활비 카드 정지해줘.", None),
        ("아까 이체가 됐어?", None),
    ]:
        result = graph.invoke({"messages": [("user", text)]}, config)
        assert ("__interrupt__" in result) == bool(action)  # 불가면 승인 요청 없이 끝나야 한다
        if action:
            result = graph.invoke(Command(resume={"action": action}), config)
        print(f"요청: {text} ({action or '승인 요청 없음'})\n답변: {result['messages'][-1].content}\n")
    assert "생활비: 1,331,800원" in functions.lookup_accounts()  # 승인한 10만 원만 반영
    assert "생활비 카드 (card-001, 체크): 분실 정지" in functions.lookup_cards()
    statuses = [r["status"] for r in read_data()["requests"]]
    assert statuses == ["failed", "completed", "rejected", "failed", "completed", "failed"], statuses
    reset_data()
    print("graph 확인 완료")
