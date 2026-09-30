# 사용자 입력을 반복해서 받고 그래프의 응답을 출력합니다.
# 같은 대화 세션을 유지하고 승인·거절 입력과 종료 명령을 처리합니다.
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
    if user_input:
        result = graph.invoke({"messages": [("user", user_input)]}, config)
        print("답변:", result["messages"][-1].content)
