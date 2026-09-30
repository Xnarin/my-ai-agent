# 선택한 계좌·이체·카드·청구서 업무를 Python 함수로 구현합니다.
# 대상과 처리 조건을 검증하고 데이터를 조회하거나 변경합니다.
# 그래프의 노드가 이 함수들을 직접 호출합니다. (Tool로 감싸지 않음)
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from data_store import read_data, reset_data, save_data

OWNER_ID = "user-001"
KST = timezone(timedelta(hours=9))
CARD_TYPES = {"credit": "신용", "debit": "체크"}
CARD_STATUS = {"active": "사용 가능", "locked": "일시 잠금", "lost": "분실 정지"}


def find_account(data, nickname):
    """본인 계좌 중에서 별명이 같은 계좌를 찾는다. 다른 사용자도 같은 별명을 쓰므로 소유자로 먼저 거른다."""
    return next(
        (a for a in data["accounts"] if a["owner_id"] == OWNER_ID and a["nickname"] == nickname),
        None,
    )


def lookup_accounts():
    """본인 계좌의 별명과 잔액을 한 줄씩 반환한다."""
    data = read_data()
    return "\n".join(
        f"{a['nickname']}: {a['balance']:,}원" for a in data["accounts"] if a["owner_id"] == OWNER_ID
    )


def check_transfer(from_name, to_name, amount):
    """이체할 수 없으면 이유나 되물을 질문을, 할 수 있으면 빈 문자열을 반환한다. (설계의 검사 순서 1~8)"""
    data = read_data()
    names = [a["nickname"] for a in data["accounts"] if a["owner_id"] == OWNER_ID]
    # 빠진 정보는 하나씩 되묻고, 고를 수 있는 계좌를 함께 보여 준다.
    if not from_name:
        return f"어느 계좌에서 보낼까요? ({', '.join(n for n in names if n != to_name)})"
    if not to_name:
        return f"어느 계좌로 보낼까요? ({', '.join(n for n in names if n != from_name)})"
    if amount is None:
        return "얼마를 보낼까요?"
    source = find_account(data, from_name)
    target = find_account(data, to_name)
    if source is None:
        return f"'{from_name}' 계좌를 찾을 수 없습니다. ({', '.join(names)} 중에서 골라 주세요)"
    if target is None:
        return f"'{to_name}' 계좌를 찾을 수 없습니다. ({', '.join(names)} 중에서 골라 주세요)"
    if source["account_id"] == target["account_id"]:
        return "출금 계좌와 입금 계좌가 같습니다."
    if amount <= 0:
        return "이체 금액은 0원보다 커야 합니다."
    if source["balance"] < amount:
        return f"잔액이 부족합니다. (현재 잔액 {source['balance']:,}원)"
    return ""


def transfer(from_name, to_name, amount):
    """이체를 실행하고 결과 문장을 반환한다. 잔액·거래 내역을 한 번에 저장한다."""
    # 승인을 기다리는 동안 잔액이 바뀌었을 수 있으니 실행 직전에 한 번 더 검사한다.
    error = check_transfer(from_name, to_name, amount)
    if error:
        raise ValueError(error)

    data = read_data()
    source = find_account(data, from_name)
    target = find_account(data, to_name)
    source["balance"] -= amount
    target["balance"] += amount
    now = datetime.now(KST).isoformat(timespec="seconds")
    for account, kind in [(source, "withdrawal"), (target, "deposit")]:
        data["transactions"].append({
            "transaction_id": str(uuid4()),
            "owner_id": account["owner_id"],
            "account_id": account["account_id"],
            "type": kind,
            "amount": amount,
            "occurred_at": now,
            "card_id": None,
            "merchant": None,
        })
    save_data(data)
    return (
        f"{from_name} → {to_name} {amount:,}원 이체 완료 "
        f"(이체 후 잔액: {from_name} {source['balance']:,}원, {to_name} {target['balance']:,}원)"
    )


def find_card(data, name):
    """본인 카드 중에서 이름이 같은 카드를 찾는다. 다른 사용자도 같은 이름을 쓰므로 소유자로 먼저 거른다."""
    return next((c for c in data["cards"] if c["owner_id"] == OWNER_ID and c["name"] == name), None)


def lookup_cards():
    """본인 카드의 이름·ID·종류·상태를 한 줄씩 반환한다."""
    data = read_data()
    return "\n".join(
        f"{c['name']} ({c['card_id']}, {CARD_TYPES[c['card_type']]}): {CARD_STATUS[c['status']]}"
        for c in data["cards"] if c["owner_id"] == OWNER_ID
    )


def check_card_lost(card_name):
    """분실 정지할 수 없으면 이유나 되물을 질문을, 할 수 있으면 빈 문자열을 반환한다.
    사용 가능한 카드와 일시 잠금된 카드는 모두 분실 정지할 수 있다."""
    data = read_data()
    names = ", ".join(c["name"] for c in data["cards"] if c["owner_id"] == OWNER_ID)
    if not card_name:
        return f"어느 카드를 정지할까요? ({names})"
    card = find_card(data, card_name)
    if card is None:
        return f"'{card_name}'에 해당하는 카드가 없습니다. ({names} 중에서 골라 주세요)"
    if card["status"] == "lost":
        return f"{card_name}는 이미 분실 정지되어 있습니다."
    return ""


def report_card_lost(card_name):
    """카드를 분실 정지하고 결과 문장을 반환한다. 계좌 잔액과 거래 내역은 바꾸지 않는다."""
    data = read_data()
    card = find_card(data, card_name)
    card["status"] = "lost"
    save_data(data)
    return f"{card_name} ({card['card_id']}) 분실 정지 완료"


if __name__ == "__main__":
    # 동작 확인: 불가 조건 8개와 이체 결과, 카드 분실 정지를 본다. (시작과 끝에 작업용 데이터를 초기화함)
    reset_data()
    print(lookup_accounts())
    assert check_transfer(None, "저축", 100000) == "어느 계좌에서 보낼까요? (생활비, 여행 자금)"
    assert check_transfer("생활비", None, 100000) == "어느 계좌로 보낼까요? (저축, 여행 자금)"
    assert check_transfer("생활비", "저축", None) == "얼마를 보낼까요?"
    not_found = "'비상금' 계좌를 찾을 수 없습니다. (생활비, 저축, 여행 자금 중에서 골라 주세요)"
    assert check_transfer("비상금", "저축", 100000) == not_found
    assert check_transfer("생활비", "비상금", 100000) == not_found
    assert check_transfer("생활비", "생활비", 100000) == "출금 계좌와 입금 계좌가 같습니다."
    assert check_transfer("생활비", "저축", -10000) == "이체 금액은 0원보다 커야 합니다."
    assert check_transfer("생활비", "저축", 99_999_999) == "잔액이 부족합니다. (현재 잔액 1,431,800원)"
    assert check_transfer("생활비", "저축", 100000) == ""

    print(transfer("생활비", "저축", 100000))
    data = read_data()
    balances = {a["account_id"]: a["balance"] for a in data["accounts"]}
    assert balances["acc-001"] == 1_331_800 and balances["acc-002"] == 2_380_000
    assert balances["acc-004"] == 850_000  # 다른 사용자의 '생활비' 계좌는 그대로
    assert len(data["transactions"]) == 22

    print(lookup_cards())
    assert check_card_lost(None) == "어느 카드를 정지할까요? (생활비 카드, 여행 카드)"
    assert check_card_lost("회사 카드") == "'회사 카드'에 해당하는 카드가 없습니다. (생활비 카드, 여행 카드 중에서 골라 주세요)"
    assert check_card_lost("생활비 카드") == ""
    print(report_card_lost("생활비 카드"))
    assert check_card_lost("생활비 카드") == "생활비 카드는 이미 분실 정지되어 있습니다."
    statuses = {c["card_id"]: c["status"] for c in read_data()["cards"]}
    assert statuses["card-001"] == "lost" and statuses["card-003"] == "active"  # 다른 사용자의 '생활비 카드'는 그대로
    reset_data()
    print("functions 확인 완료")
