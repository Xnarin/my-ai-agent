import json
from typing import Literal

from langchain_core.tools import tool


WEATHER_DATA = {
    "서울": "맑음, 22도, 습도 45%",
    "부산": "흐림, 19도, 습도 72%",
    "제주": "비, 17도, 습도 88%",
}

MOVIES = {
    101: {
        "id": 101,
        "title": "달빛 우체국",
        "release_date": "2026-10-01",
        "overview": "작은 마을의 집배원이 주인을 찾지 못한 편지를 배달한다.",
        "genres": ["드라마", "판타지"],
        "runtime_minutes": 112,
    },
    102: {
        "id": 102,
        "title": "마지막 기차",
        "release_date": "2026-10-08",
        "overview": "막차에 탑승한 승객들이 사라진 기관사를 찾아 나선다.",
        "genres": ["미스터리"],
        "runtime_minutes": 105,
    },
    103: {
        "id": 103,
        "title": "우리 동네 로봇",
        "release_date": "2026-10-15",
        "overview": "길을 잃은 로봇이 동네 사람들의 도움으로 집을 찾아간다.",
        "genres": ["가족", "SF"],
        "runtime_minutes": 98,
    },
    104: {
        "id": 104,
        "title": "파도 너머",
        "release_date": "2026-10-22",
        "overview": "서로 다른 이유로 바다를 찾은 두 사람이 수영 대회를 준비한다.",
        "genres": ["드라마"],
        "runtime_minutes": 120,
    },
    105: {
        "id": 105,
        "title": "수상한 빵집",
        "release_date": "2026-10-23",
        "overview": "초보 제빵사가 매일 밤 사라지는 빵의 행방을 추적한다.",
        "genres": ["코미디", "미스터리"],
        "runtime_minutes": 102,
    },
    106: {
        "id": 106,
        "title": "겨울의 지도",
        "release_date": "2026-12-03",
        "overview": "남매가 오래된 지도에 표시된 장소를 찾아 겨울 여행을 떠난다.",
        "genres": ["모험", "가족"],
        "runtime_minutes": 115,
    },
}

MOVIE_LISTS = {
    "popular": [103, 101, 105, 102, 104],
    "now_playing": [101, 102, 103, 104, 105],
    "upcoming": [106],
}


@tool(parse_docstring=True)
def search_weather(city: str) -> str:
    """도시별 날씨를 고정된 실습용 데이터에서 조회한다. 실제 날씨가 아니다.

    Args:
        city: 날씨를 조회할 도시 이름. 예: '서울', '부산', '제주'
    """
    return WEATHER_DATA.get(city, f"{city}의 날씨 정보를 찾을 수 없습니다.")


@tool(parse_docstring=True)
def get_movie_list(
    category: Literal["popular", "now_playing", "upcoming"],
    limit: int = 5,
) -> str:
    """분류별 가상 영화의 ID, 제목, 개봉일을 조회한다. 고정된 실습용 데이터이다.

    Args:
        category: 목록 분류. popular은 인기, now_playing은 현재 상영, upcoming은 개봉 예정이다.
        limit: 반환할 최대 영화 수. 1개 이상 20개 이하로 지정한다.
    """
    if not 1 <= limit <= 20:
        return "오류: limit은 1 이상 20 이하이어야 합니다."

    movies = [
        {key: MOVIES[movie_id][key] for key in ("id", "title", "release_date")}
        for movie_id in MOVIE_LISTS[category][:limit]
    ]
    return json.dumps(movies, ensure_ascii=False)


@tool(parse_docstring=True)
def get_movie_detail(movie_id: int) -> str:
    """가상 영화 ID로 제목, 줄거리, 장르, 러닝타임, 개봉일을 조회한다.

    Args:
        movie_id: 영화 목록 조회 결과에 포함된 영화 ID.
    """
    movie = MOVIES.get(movie_id)
    if movie is None:
        return f"영화 ID {movie_id}의 정보를 찾을 수 없습니다."
    return json.dumps(movie, ensure_ascii=False)
