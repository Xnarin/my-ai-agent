"""조사 항목 분해, 관점별 분석, 종합 노드."""

from typing import TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from .prompts import ASPECTS_PROMPT, RESEARCH_PROMPT, SYNTHESIS_PROMPT


class ResearchState(TypedDict, total=False):
    request: str
    conversation: str
    aspects: list[str]
    findings: list[str]
    result: str


class ResearchAspects(BaseModel):
    aspects: list[str] = Field(description="서로 다른 조사 관점 1~3개")


def build_nodes(model: ChatGoogleGenerativeAI):
    def plan_aspects(state: ResearchState) -> dict:
        response = model.with_structured_output(ResearchAspects).invoke([
            ("system", ASPECTS_PROMPT),
            ("human", f"이전 대화:\n{state.get('conversation', '')}\n\n요청:\n{state['request']}"),
        ])
        aspects = [item.strip() for item in response.aspects if item.strip()][:3]
        return {"aspects": aspects or ["요청의 핵심 조건과 선택지"]}

    def investigate(state: ResearchState) -> dict:
        findings = []
        for aspect in state["aspects"]:
            response = model.invoke([
                ("system", RESEARCH_PROMPT),
                ("human", f"이전 대화:\n{state.get('conversation', '')}\n\n"
                 f"사용자 요청:\n{state['request']}\n\n조사 관점: {aspect}"),
            ])
            findings.append(f"[{aspect}]\n{response.text}")
        return {"findings": findings}

    def synthesize(state: ResearchState) -> dict:
        response = model.invoke([
            ("system", SYNTHESIS_PROMPT),
            ("human", "사용자 요청:\n" + state["request"] + "\n\n관점별 분석:\n"
             + "\n\n".join(state["findings"])),
        ])
        return {"result": response.text}

    return plan_aspects, investigate, synthesize
