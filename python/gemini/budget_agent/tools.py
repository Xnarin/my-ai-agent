add_transaction_tool = {
    "type": "function",
    "name": "add_transaction",
    "description": "새 거래 내역을 저장합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "description": "거래 유형. 수입 또는 지출",
                "enum": ["수입", "지출"],
            },
            "category": {
                "type": "string",
                "description": "거래 카테고리. 예: 식비, 교통, 급여",
            },
            "amount": {
                "type": "integer",
                "description": "거래 금액. 0원 이상",
                "minimum": 0,
            },
            "description": {
                "type": "string",
                "description": "거래 설명. 예: 점심 식사",
            },
            "date": {
                "type": "string",
                "description": "거래 날짜. YYYY-MM-DD 형식. 예: 2026-08-28",
            },
        },
        "required": [
            "type",
            "category",
            "amount",
            "description",
            "date",
        ],
    },
}


search_transactions_tool = {
    "type": "function",
    "name": "search_transactions",
    "description": "날짜, 카테고리 혹은 설명을 받아서 저장된 거래 내역을 찾는다.",
    "parameters": {
        "type": "object",
        "properties": {
            "date": {
                "type": "string",
                "description": "검색할 거래 날짜. ex) 2026-08-28",
            },
            "category": {
                "type": "string",
                "description": "검색할 카테고리. ex) 식비",
            },
            "description": {
                "type": "string",
                "description": "거래 설명에 포함된 단어. ex) 점심",
            },
        },
        "required": [],
    },
}

update_transaction_tool = {
    "type": "function",
    "name": "update_transaction",
    "description": "기존 거래 내역을 수정합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "id": {
                "type": "string",
                "description": "수정할 거래 ID",
            },
            "type": {
                "type": "string",
                "enum": ["수입", "지출"],
            },
            "category": {
                "type": "string",
            },
            "amount": {
                "type": "integer",
                "minimum": 0,
            },
            "description": {
                "type": "string",
            },
            "date": {
                "type": "string",
                "description": "YYYY-MM-DD 형식",
            },
        },
        "required": ["id"],
    },
}

set_budget_tool = {
    "type": "function",
    "name": "set_budget",  # 여기 수정
    "description": "특정 월과 카테고리의 예산을 설정하거나 수정합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "month": {
                "type": "string",
                "description": "예산을 설정할 연월. 예: 2026-08",
            },
            "category": {
                "type": "string",
                "description": "예산 카테고리. 예: 식비",
            },
            "amount": {
                "type": "integer",
                "description": "설정할 예산 금액",
                "minimum": 0,
            },
        },
        "required": ["month", "category", "amount"],
    },
}

check_budget_tool = {
    "type": "function",
    "name": "check_budget",
    "description": "특정 월과 카테고리의 예산, 실제 지출, 남은 예산을 조회합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "month": {
                "type": "string",
                "description": "조회할 연월. YYYY-MM 형식. 예: 2026-08",
            },
            "category": {
                "type": "string",
                "description": "조회할 예산 카테고리. 예: 식비, 교통",
            },
        },
        "required": ["month", "category"],
    },
}

export_monthly_doc_tool = {
    "type": "function",
    "name": "export_monthly_doc",
    "description": "특정 월의 거래 내역을 Word 문서 파일로 저장합니다.",
    "parameters": {
        "type": "object",
        "properties": {
            "month": {
                "type": "string",
                "description": "저장할 연월. 예: 2026-08",
            },
        },
        "required": ["month"],
    },
}

# 도구와 함수 연결

from services import (
    add_transaction,
    search_transactions,
    update_transaction,
    set_budget,
    check_budget,
    export_monthly_doc,
)

TOOLS = [
    add_transaction_tool,
    search_transactions_tool,
    update_transaction_tool,
    set_budget_tool,
    check_budget_tool,
    export_monthly_doc_tool,
]

TOOL_FUNCTIONS = {
    "add_transaction": add_transaction,
    "search_transactions": search_transactions,
    "update_transaction": update_transaction,
    "set_budget": set_budget,
    "check_budget": check_budget,
    "export_monthly_doc": export_monthly_doc,
}