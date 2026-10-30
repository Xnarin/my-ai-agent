from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from fastapi_agent.domains.comments.models import Comment
from fastapi_agent.domains.comments.schemas import CommentCreate


class CommentRepository:
    async def save(self, db: AsyncSession, comment: Comment) -> Comment:
        db.add(comment)
        await db.flush()
        await db.refresh(comment, attribute_names=["user"])
        return comment

    async def find_by_post_id(self, db: AsyncSession, post_id: int) -> Sequence[Comment]:
        result = await db.scalars(
            select(Comment)
            .options(joinedload(Comment.user))
            .where(Comment.post_id == post_id)
            .order_by(Comment.id)
        )
        return result.all()

    async def find_by_id(
        self, db: AsyncSession, post_id: int, comment_id: int
    ) -> Comment | None:
        return await db.scalar(
            select(Comment)
            .options(joinedload(Comment.user))
            .where(Comment.post_id == post_id, Comment.id == comment_id)
        )

    def update(self, db: AsyncSession, comment: Comment, data: CommentCreate) -> Comment:
        comment.content = data.content
        return comment

    async def delete(self, db: AsyncSession, comment: Comment) -> None:
        await db.delete(comment)


comment_repository = CommentRepository()
