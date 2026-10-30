from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph.state import CompiledStateGraph

from agents.chatbot.tools import get_movie_detail, get_movie_list, search_weather


SYSTEM_PROMPT = """당신은 날씨와 영화 정보를 안내하는 한국어 챗봇입니다.
날씨와 영화 정보는 제공된 도구로 조회하고, 실습용 더미 데이터임을 안내하세요.
영화 목록에는 줄거리와 러닝타임이 없으므로 상세 정보가 필요하면 상세 조회 도구를 사용하세요.
'그중', '첫 번째', '그 도시' 같은 표현은 현재 대화의 메시지와 도구 결과를 기준으로 해석하세요.
현재 대화에 필요한 맥락이 없으면 대상 도시나 영화를 물어보세요.
도구에 정보가 없거나 오류가 발생하면 내용을 추측하지 말고 조회 결과를 안내하세요."""


def create_chat_agent(
    checkpointer: BaseCheckpointSaver | None,
    *,
    model: BaseChatModel | None = None,
) -> CompiledStateGraph:
    if model is None:
        model = ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            timeout=30,
            max_retries=2,
        )

    return create_agent(
        model=model,
        tools=[search_weather, get_movie_list, get_movie_detail],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        name="chat_agent",
    ).with_config(recursion_limit=20)
