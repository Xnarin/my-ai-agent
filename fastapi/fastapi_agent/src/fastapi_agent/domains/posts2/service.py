from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_agent.domains.posts2.models import Post2
from fastapi_agent.domains.posts2.repository import post2_repository
from fastapi_agent.domains.posts2.schemas import (
    Post2PageResponse,
    Post2Query,
    Post2Response,
    Post2SetupResponse,
)


class Post2Service:
    async def setup(self, db: AsyncSession, count: int) -> Post2SetupResponse:
        topics = [
            ("backend", "FastAPI", "API 요청과 응답을 다룹니다."),
            ("backend", "SQLAlchemy", "데이터베이스 조회와 트랜잭션을 다룹니다."),
            ("frontend", "React", "컴포넌트와 상태 관리를 다룹니다."),
            ("frontend", "JavaScript", "브라우저 이벤트와 비동기 요청을 다룹니다."),
            ("ai", "LangChain", "검색 증강 생성과 문서 검색을 다룹니다."),
            ("ai", "Agent", "도구 호출과 대화 흐름을 다룹니다."),
        ]
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        posts = []
        for number in range(1, count + 1):
            category, topic, content = topics[(number - 1) % len(topics)]
            posts.append(
                Post2(
                    title=f"{topic} 실습 {number:04d}",
                    content=f"{content} 예제 {number}의 실습 기록입니다.",
                    category=category,
                    views=(number * 37 % 10) * 100,
                    created_at=start + timedelta(days=(number - 1) // 20),
                )
            )

        async with db.begin():
            await post2_repository.replace_all(db, posts)
        return Post2SetupResponse(count=count)

    async def get_posts(
        self, db: AsyncSession, params: Post2Query
    ) -> Post2PageResponse:
        offset = (params.page - 1) * params.size
        posts, total = await post2_repository.find_page(db, params, offset)
        total_pages = (total + params.size - 1) // params.size
        return Post2PageResponse(
            items=[Post2Response.model_validate(post) for post in posts],
            total=total,
            page=params.page,
            size=params.size,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1 and total > 0,
        )


post2_service = Post2Service()
