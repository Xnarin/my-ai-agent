# 사용자 입력을 반복해서 받고 그래프의 응답을 출력합니다.
# 같은 대화 세션을 유지하고 승인·거절 입력과 종료 명령을 처리합니다.
from langgraph.types import Command

from data_store import prepare_data
from graph import graph

prepare_data()
# MemorySaver는 실행 중에만 기억하므로 thread_id는 고정값이면 충분하다.
config = {"configurable": {"thread_id": "main"}}
print("가상 금융 에이전트 (종료: /exit)")

while True:
    user_input = input("\n요청: ").strip()
    if user_input == "/exit":
        break
    if not user_input:
        continue
    result = graph.invoke({"messages": [("user", user_input)]}, config)
    # 승인 요청에서 멈추면 사용자 답을 받아 이어서 실행한다.
    while "__interrupt__" in result:
        request = result["__interrupt__"][0].value
        print(f"{request['question']}\n  {request['detail']}")
        answer = input("승인 / 거절: ").strip()
        while answer not in ("승인", "거절"):
            answer = input("'승인' 또는 '거절'을 입력하세요: ").strip()
        action = "approve" if answer == "승인" else "reject"
        result = graph.invoke(Command(resume={"action": action}), config)
    print("답변:", result["messages"][-1].content)
