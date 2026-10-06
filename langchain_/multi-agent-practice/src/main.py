"""같은 세션에서 후속 요청을 이어서 처리하는 콘솔 앱."""

import uuid

from dotenv import find_dotenv, load_dotenv
from langchain_core.messages import HumanMessage

from graph import create_workflow


def main() -> None:
    load_dotenv(find_dotenv(usecwd=True))
    graph = create_workflow()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    print("요청을 입력하세요. 종료하려면 '종료' 또는 'exit'를 입력하세요.")

    while True:
        try:
            request = input("\n요청> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break
        if request.lower() in {"종료", "exit", "quit"}:
            print("종료합니다.")
            break
        if not request:
            continue
        try:
            result = graph.invoke({"messages": [HumanMessage(content=request)]}, config)
        except Exception as exc:
            print(f"처리 중 오류가 발생했습니다: {exc}")
            continue
        print("\n실제 실행:", " → ".join(result["executed"]))
        print("\n응답:\n" + result["last_answer"])


if __name__ == "__main__":
    main()

