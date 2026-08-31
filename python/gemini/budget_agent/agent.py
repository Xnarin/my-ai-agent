import json
import os
from datetime import date as Date

from dotenv import load_dotenv
from google import genai

from tools import TOOLS, TOOL_FUNCTIONS

# gemini 연결 준비
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError(".env 파일에 GEMINI_API_KEY를 설정해 주세요.")

model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
client = genai.Client(api_key=api_key)

SYSTEM_INSTRUCTION = f"""
너는 내 가계부 도와주는 에이전트야.
오늘은 {Date.today().isoformat()}이야.

- 수입이나 지출 얘기 나오면 add_transaction으로 바로 저장해.
- 날짜 없으면 오늘 날짜로 넣어.
- 거래 검색은 search_transactions를 써.
- 수정 요청인데 ID가 없으면 먼저 검색해.
- 예산 설정은 set_budget, 예산 확인은 check_budget을 써.
- 문서 저장 요청은 export_monthly_doc을 써.
"""

def execute_tool_call(step) -> dict:
    tool_function = TOOL_FUNCTIONS.get(step.name)
    if tool_function is None:
        return {"ok": False, "error": f"허용되지 않은 도구: {step.name}"}

    try:
        return tool_function(**step.arguments)
    except TypeError as error:
        return {"ok": False, "error": f"잘못된 인자: {error}"}
    except Exception as error:
        return {"ok": False, "error": f"도구 실행 실패: {type(error).__name__}"}

def run_agent(user_input: str, max_turns: int = 5) -> dict:
    next_input = user_input
    previous_interaction_id = None
    logs = []

    for turn in range(1, max_turns + 1):
        request = {
            "model": model,
            "input": next_input,
            "tools": TOOLS,
            "system_instruction": SYSTEM_INSTRUCTION,
            "store": True,
        }
        if previous_interaction_id is not None:
            request["previous_interaction_id"] = previous_interaction_id

        interaction = client.interactions.create(**request)
        function_calls = [step for step in interaction.steps if step.type == "function_call"]

        if not function_calls:
            return {
                "ok": True,
                "answer": interaction.output_text,
                "turns": turn,
                "tool_logs": logs,
            }

        next_input = []
        for step in function_calls:
            result = execute_tool_call(step)
            logs.append({"turn": turn, "tool": step.name, "arguments": step.arguments, "result": result})
            next_input.append({
                "type": "function_result",
                "name": step.name,
                "call_id": step.id,
                "result": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
            })

        previous_interaction_id = interaction.id

    return {
        "ok": False,
        "answer": None,
        "turns": max_turns,
        "tool_logs": logs,
        "error": "최대 반복 횟수를 초과했습니다.",
    }
