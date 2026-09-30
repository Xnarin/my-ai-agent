# 원본 JSON의 복사본을 작업용 데이터로 준비합니다.
# 작업용 JSON을 읽고 변경된 데이터를 저장하는 함수를 구현합니다.
# 초기화가 필요할 때만 원본을 다시 복사합니다.
import json
from pathlib import Path
from shutil import copyfile

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INITIAL_PATH = DATA_DIR / "initial_data.json"
DATA_PATH = DATA_DIR / "data.json"


def reset_data():
    copyfile(INITIAL_PATH, DATA_PATH)


def prepare_data():
    if not DATA_PATH.exists():
        reset_data()


def read_data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def save_data(data):
    # 임시 파일에 다 쓴 뒤 교체한다. 쓰다가 실패해도 기존 파일은 그대로 남는다.
    temp_path = DATA_PATH.with_suffix(".tmp")
    temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(DATA_PATH)


if __name__ == "__main__":
    # 동작 확인: 저장한 값이 다시 읽히는지, 초기화되는지 본다. (실행하면 작업용 데이터가 초기화됨)
    prepare_data()
    data = read_data()
    data["accounts"][0]["balance"] += 1000
    save_data(data)
    assert read_data()["accounts"][0]["balance"] == data["accounts"][0]["balance"]
    reset_data()
    assert read_data() == json.loads(INITIAL_PATH.read_text(encoding="utf-8"))
    print("data_store 확인 완료")
