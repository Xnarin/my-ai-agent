"""초안의 문제를 찾고 현실적인 개선안을 작성합니다."""

from langchain_google_genai import ChatGoogleGenerativeAI


REVIEW_PROMPT = """당신은 계획 검토 담당자입니다.
현재 요청의 필수 조건, 실현 가능성, 일관성, 누락을 확인하세요.
문제점과 이유를 짧게 설명한 뒤, 문제를 해결한 '개선된 최종안'을 완성된 형태로 작성하세요.
사용자가 초안을 주었다면 그 초안을 검토하고, 앞 단계 계획이 있으면 그 계획을 검토하세요.
앞 단계 조사 결과가 있으면 그것과 충돌하지 않게 개선하세요.
예산·인력 등 명시한 조건과 이전 대화의 확정 내용을 지키세요.
근거 없는 시장 수치나 추정은 사실처럼 제시하지 말고 '가정'이라고 표시하세요.
이전 결과 중 일부를 수정하라는 후속 요청은 다른 내용을 유지하세요."""


def create_reviewer(model: ChatGoogleGenerativeAI):
    def review(request: str, conversation: str, research: str, draft: str) -> str:
        response = model.invoke([
            ("system", REVIEW_PROMPT),
            ("human", f"이전 대화:\n{conversation}\n\n현재 요청:\n{request}\n\n"
             f"조사 결과:\n{research or '없음'}\n\n검토할 초안:\n{draft}"),
        ])
        return response.text

    return review
