"""요청별 역할 선택과 조사 → 기획 → 검토 흐름."""

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from agents.planning import create_planner
from agents.research.graph import create_research_graph
from agents.review import create_reviewer


Role = Literal["research", "planning", "review"]
ROLE_NAMES = {"research": "조사", "planning": "기획", "review": "검토"}
ROLE_ORDER = ("research", "planning", "review")


class WorkflowState(TypedDict, total=False):
    messages: Annotated[list, add_messages]
    roles: list[Role]
    role_index: int
    executed: list[str]
    previous_answer: str
    research_result: str
    plan_result: str
    review_result: str
    last_answer: str


class RoleSelection(BaseModel):
    roles: list[Role] = Field(description="이번 요청에 실제로 필요한 역할만 선택")


ROUTING_PROMPT = """이번 사용자 요청에 필요한 역할만 고르세요.
research: 정보·선택지의 조사, 비교, 분석.
planning: 목표를 위한 새 실행 계획 작성 또는 이전 계획 수정.
review: 사용자가 제공한 초안 또는 작성된 계획의 문제 검토와 개선.
명시적으로 하지 말라는 역할은 절대 선택하지 마세요.
조사만 요청하면 research만, 추가 조사 없는 계획은 planning만,
초안 검토만 요청하면 review만 선택하세요.
조사 후 계획, 계획 검토를 모두 요청하면 세 역할을 선택하세요.
이전 계획의 일부만 바꾸라는 후속 요청은 planning만 선택하세요.
역할 순서는 중요하지 않습니다. 역할 이름만 반환하세요."""


def conversation_text(messages: list, *, exclude_latest: bool = True) -> str:
    previous = messages[:-1] if exclude_latest else messages
    return "\n\n".join(
        f"{'사용자' if isinstance(message, HumanMessage) else '응답'}: {message.content}"
        for message in previous[-8:]
        if isinstance(message, (HumanMessage, AIMessage))
    )


def create_workflow(model: ChatGoogleGenerativeAI | None = None):
    model = model or ChatGoogleGenerativeAI(model="gemini-3.6-flash")
    research_graph = create_research_graph(model)
    plan = create_planner(model)
    review = create_reviewer(model)

    def select_roles(state: WorkflowState) -> dict:
        request = state["messages"][-1].content
        previous = conversation_text(state["messages"])
        selection = model.with_structured_output(RoleSelection).invoke([
            ("system", ROUTING_PROMPT),
            ("human", f"이전 대화:\n{previous}\n\n이번 요청:\n{request}"),
        ])
        selected = set(selection.roles)
        roles = [role for role in ROLE_ORDER if role in selected]
        if not roles:
            roles = ["planning"]
        print("실행 순서:", " → ".join(ROLE_NAMES[role] for role in roles))
        return {
            "roles": roles,
            "role_index": 0,
            "executed": [],
            "previous_answer": state.get("last_answer", ""),
            "research_result": "",
            "plan_result": "",
            "review_result": "",
        }

    def run_research(state: WorkflowState) -> dict:
        print("[에이전트 실행] 조사")
        request = state["messages"][-1].content
        result = research_graph.invoke({
            "request": request,
            "conversation": conversation_text(state["messages"]),
        })
        return {"research_result": result["result"], "executed": state["executed"] + ["조사"]}

    def run_planning(state: WorkflowState) -> dict:
        print("[에이전트 실행] 기획")
        result = plan(
            state["messages"][-1].content,
            conversation_text(state["messages"]),
            state.get("research_result", ""),
            state.get("previous_answer", ""),
        )
        return {"plan_result": result, "executed": state["executed"] + ["기획"]}

    def run_review(state: WorkflowState) -> dict:
        print("[에이전트 실행] 검토")
        draft = state.get("plan_result") or state["messages"][-1].content
        result = review(
            state["messages"][-1].content,
            conversation_text(state["messages"]),
            state.get("research_result", ""),
            draft,
        )
        return {"review_result": result, "executed": state["executed"] + ["검토"]}

    def advance(state: WorkflowState) -> dict:
        return {"role_index": state["role_index"] + 1}

    def next_role(state: WorkflowState) -> str:
        if state["role_index"] >= len(state["roles"]):
            return "finish"
        return state["roles"][state["role_index"]]

    def finish(state: WorkflowState) -> dict:
        answer = (state.get("review_result") or state.get("plan_result")
                  or state.get("research_result") or "처리할 요청을 찾지 못했습니다.")
        return {"last_answer": answer, "messages": [AIMessage(content=answer)]}

    builder = StateGraph(WorkflowState)
    builder.add_node("select_roles", select_roles)
    builder.add_node("research", run_research)
    builder.add_node("planning", run_planning)
    builder.add_node("review", run_review)
    builder.add_node("advance", advance)
    builder.add_node("finish", finish)
    builder.add_edge(START, "select_roles")
    destinations = {"research": "research", "planning": "planning",
                    "review": "review", "finish": "finish"}
    builder.add_conditional_edges("select_roles", next_role, destinations)
    for role in ROLE_ORDER:
        builder.add_edge(role, "advance")
    builder.add_conditional_edges("advance", next_role, destinations)
    builder.add_edge("finish", END)
    return builder.compile(checkpointer=InMemorySaver())
