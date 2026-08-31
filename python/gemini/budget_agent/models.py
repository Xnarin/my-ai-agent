from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Transaction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_id: str = Field(
        description="거래를 구분하는 고유 ID. ex) T001"
    )
    transaction_type: Literal["수입", "지출"] = Field(
        description="거래 유형"
    )
    category: str = Field(
        description="거래 카테고리. ex) 식비, 교통, 급여"
    )
    amount: int = Field(
        ge=0,
        description="거래 금액. 0원 이상"
    )
    description: str = Field(
        max_length=100,
        description="거래에 관한 간단한 설명"
    )
    transaction_date: date = Field(
        description="거래 날짜. ex) 2026-08-28"
    )

# Pydantic 모델을 Gemini에 전달할 JSON Schema로 변환
# transaction_schema = Transaction.model_json_schema()