"""조사 에이전트를 구성합니다."""

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, START, StateGraph

from .nodes import ResearchState, build_nodes


def create_research_graph(model: ChatGoogleGenerativeAI):
    plan_aspects, investigate, synthesize = build_nodes(model)
    builder = StateGraph(ResearchState)
    builder.add_node("plan_aspects", plan_aspects)
    builder.add_node("investigate", investigate)
    builder.add_node("synthesize", synthesize)
    builder.add_edge(START, "plan_aspects")
    builder.add_edge("plan_aspects", "investigate")
    builder.add_edge("investigate", "synthesize")
    builder.add_edge("synthesize", END)
    return builder.compile()
