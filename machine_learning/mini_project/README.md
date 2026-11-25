# 신용평가 미니 프로젝트 — 실행 안내

UCI Default of Credit Card Clients(30,000명)로 다음 달 카드 대금 연체 여부를 예측한다.

## 파일

| 파일 | 내용 |
| --- | --- |
| `credit_scroing.ipynb` | 실행 코드 (데이터 로딩 → 탐색 → 분할 → 전처리 → 모델 비교 → 실험 → 테스트 → 사례 분석 → 추세 변수·교차 검증 추가 실험) |
| `실험기록.md` | 초기 계획, 실험 비교표, 최종 모델과 테스트 결과, 사례 분석, 회고 |
| `project.md` | 과제 설명 + 단계별 진행·테스트 기록 |
| `data/` | 노트북 실행 시 `default_credit_clients.csv`가 자동으로 저장되는 곳 |

## 실행 환경

- Windows 11, Python 3.14.6 (레포 루트의 `.venv`)
- 확인한 패키지 버전: pandas 3.0.5, scikit-learn 1.9.1, xgboost 3.4.1, lightgbm 4.7.0, matplotlib 3.11.2
- 그래프 한글 폰트로 `Malgun Gothic`(Windows 기본)을 쓴다. 다른 OS에서는 노트북 3번째 셀의 폰트 이름을 바꾼다.

## 설치

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install pandas scikit-learn xgboost lightgbm matplotlib ipykernel nbconvert
```

## 데이터 준비

따로 할 일은 없다. 노트북의 "데이터 다운로드" 셀이 UCI에서 CSV를 받아 `data/default_credit_clients.csv`로 저장하고, 파일이 있으면 다시 받지 않는다. 인터넷 연결이 필요하다.

## 실행 순서

노트북을 위에서부터 순서대로 실행한다. 새 커널에서 전체 실행에 약 1분 걸린다.

명령줄에서 새 커널로 처음부터 실행하려면 (`mini_project` 폴더에서):

```powershell
python -m jupyter nbconvert --to notebook --execute --inplace credit_scroing.ipynb
```

난수 시드는 `SEED = 42`로 고정되어 있어 같은 환경이면 같은 결과가 나온다.
