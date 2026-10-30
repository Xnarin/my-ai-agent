from collections.abc import Sequence

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_agent.domains.posts2.models import Post2
from fastapi_agent.domains.posts2.schemas import Post2Query


class Post2Repository:
    async def replace_all(self, db: AsyncSession, posts: list[Post2]) -> None:
        await db.execute(delete(Post2))
        db.add_all(posts)
        await db.flush()

    async def find_page(
        self, db: AsyncSession, params: Post2Query, offset: int
    ) -> tuple[Sequence[Post2], int]:
        conditions = []
        if params.keyword is not None:
            conditions.append(
                or_(
                    Post2.title.icontains(params.keyword, autoescape=True),
                    Post2.content.icontains(params.keyword, autoescape=True),
                )
            )
        if params.category is not None:
            conditions.append(Post2.category == params.category)
        if params.min_views is not None:
            conditions.append(Post2.views >= params.min_views)

        total = await db.scalar(
            select(func.count()).select_from(Post2).where(*conditions)
        )

        sort_columns = {
            "id": Post2.id,
            "title": Post2.title,
            "created_at": Post2.created_at,
            "views": Post2.views,
        }
        column = sort_columns[params.sort_by]
        if params.order == "asc":
            ordering = [column.asc(), Post2.id.asc()]
        else:
            ordering = [column.desc(), Post2.id.desc()]

        result = await db.scalars(
            select(Post2)
            .where(*conditions)
            .order_by(*ordering)
            .offset(offset)
            .limit(params.size)
        )
        return result.all(), total


post2_repository = Post2Repository()
