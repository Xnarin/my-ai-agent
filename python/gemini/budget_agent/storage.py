import json
from pathlib import Path

from models import Transaction

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "transactions_2026_04_to_08.json"

TRANSACTIONS = {}
BUDGETS = {}


def load_data():
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    TRANSACTIONS.clear()
    BUDGETS.clear()

    for item in data["transactions"]:
        transaction = Transaction(**item)
        TRANSACTIONS[transaction.transaction_id] = transaction

    BUDGETS.update(data["budgets"])


def save_data():
    data = {
        "budgets": BUDGETS,
        "transactions": [
            transaction.model_dump(mode="json")
            for transaction in TRANSACTIONS.values()
        ],
    }

    with open(DATA_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)