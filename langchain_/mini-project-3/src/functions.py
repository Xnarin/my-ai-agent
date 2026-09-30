# 선택한 계좌·이체·카드·청구서 업무를 Python 함수로 구현합니다.
# 대상과 처리 조건을 검증하고 데이터를 조회하거나 변경합니다.
# 그래프의 노드가 이 함수들을 직접 호출합니다. (Tool로 감싸지 않음)
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from data_store import read_data, reset_data, save_data

OWNER_ID = "user-001"
KST = timezone(timedelta(hours=9))


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
    """이체할 수 없으면 이유를, 할 수 있으면 빈 문자열을 반환한다. (설계의 검사 순서 1~6)"""
    if not from_name or not to_name or amount is None:
        return "출금 계좌, 입금 계좌, 금액을 모두 알려주세요."
    data = read_data()
    source = find_account(data, from_name)
    target = find_account(data, to_name)
    if source is None:
        return f"'{from_name}' 계좌를 찾을 수 없습니다."
    if target is None:
        return f"'{to_name}' 계좌를 찾을 수 없습니다."
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


if __name__ == "__main__":
    # 동작 확인: 불가 조건 6개와 이체 결과를 본다. (시작과 끝에 작업용 데이터를 초기화함)
    reset_data()
    print(lookup_accounts())
    assert check_transfer(None, "저축", 100000) == "출금 계좌, 입금 계좌, 금액을 모두 알려주세요."
    assert check_transfer("비상금", "저축", 100000) == "'비상금' 계좌를 찾을 수 없습니다."
    assert check_transfer("생활비", "비상금", 100000) == "'비상금' 계좌를 찾을 수 없습니다."
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
    reset_data()
    print("functions 확인 완료")
