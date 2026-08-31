import storage
from agent import run_agent

storage.load_data()
while True :
    question = input("가계부 에이전트입니다 무엇을 도와드릴까요?\n")
    # 2026년 8월 식비 내역 보여줘.
    # 사용자: 오늘 점심으로 12,000원 썼어.
    # 사용자: 2026년 8월 28일 식사로 쓴 금액을 24,500원으로 수정해줘.
    # 사용자: 이번 달 식비 예산이 얼마나 남았어?
    # 사용자: 2026년 8월 지출 내역을 파일로 저장해줘.
    if question == 'q' or question == 'quit' or question == '종료' :
        break

    result = run_agent(question)
    print(result["answer"] + '\n')


