from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from fastapi_agent.domains.comments.models import Comment
from fastapi_agent.domains.posts.models import Post
from fastapi_agent.domains.posts.schemas import PostCreate


class PostRepository:
    async def save(self, db: AsyncSession, post: Post) -> Post:
        db.add(post)
        await db.flush()
        return post

    async def find_all(self, db: AsyncSession) -> Sequence[Post]:
        result = await db.scalars(
            select(Post).options(joinedload(Post.user)).order_by(Post.id)
        )
        return result.all()

    async def find_by_id(self, db: AsyncSession, post_id: int) -> Post | None:
        return await db.scalar(
            select(Post)
            .options(
                joinedload(Post.user),
                selectinload(Post.comments).joinedload(Comment.user),
            )
            .where(Post.id == post_id)
        )

    async def exists_by_id(self, db: AsyncSession, post_id: int) -> bool:
        return await db.scalar(select(Post.id).where(Post.id == post_id)) is not None

    async def find_by_user_id(self, db: AsyncSession, user_id: int) -> Sequence[Post]:
        result = await db.scalars(
            select(Post)
            .options(joinedload(Post.user))
            .where(Post.user_id == user_id)
            .order_by(Post.id)
        )
        return result.all()

    def update(self, db: AsyncSession, post: Post, data: PostCreate) -> Post:
        post.title = data.title
        post.content = data.content
        return post

    async def delete(self, db: AsyncSession, post: Post) -> None:
        await db.delete(post)


post_repository = PostRepository()
