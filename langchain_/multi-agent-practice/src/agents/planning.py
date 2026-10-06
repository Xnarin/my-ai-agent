"""조건과 조사 결과를 반영해 실행 계획을 작성합니다."""

from langchain_google_genai import ChatGoogleGenerativeAI


PLANNING_PROMPT = """당신은 실행 계획 담당자입니다.
사용자의 목표, 예산, 인력, 업종, 수정 지시를 빠뜨리지 마세요.
조사 결과가 있으면 선택 이유와 계획에 반영하세요. 없으면 외부 조사를 한 것처럼 쓰지 마세요.
목표, 우선순위, 구체적인 실행 단계, 예산·인력 제약, 검증 지표를 제시하세요.
숫자를 추정해야 한다면 '가정'이라고 명시하고 같은 가정을 일관되게 사용하세요.
이전 계획의 일부만 바꾸라는 후속 요청이면 나머지 조건과 내용을 유지하세요.
계획을 검토하거나 채점하는 설명은 작성하지 마세요."""


def create_planner(model: ChatGoogleGenerativeAI):
    def plan(request: str, conversation: str, research: str, previous: str) -> str:
        response = model.invoke([
            ("system", PLANNING_PROMPT),
            ("human", f"이전 대화:\n{conversation}\n\n이전 결과:\n{previous}\n\n"
             f"현재 요청:\n{request}\n\n조사 결과:\n{research or '추가 조사 없음'}"),
        ])
        return response.text

    return plan
