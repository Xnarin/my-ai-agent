from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_agent.core.exceptions import ForbiddenException, NotFoundException
from fastapi_agent.domains.posts.models import Post
from fastapi_agent.domains.posts.repository import post_repository
from fastapi_agent.domains.posts.schemas import PostCreate
from fastapi_agent.domains.users.schemas import UserResponse


class PostService:
    async def create_post(
        self, db: AsyncSession, data: PostCreate, current_user: UserResponse
    ) -> Post:
        async with db.begin():
            post = Post(
                title=data.title,
                content=data.content,
                user_id=current_user.id,
                comments=[],
            )
            await post_repository.save(db, post)
            result = await self.get_post(db, post.id)
        return result

    async def get_posts(self, db: AsyncSession) -> Sequence[Post]:
        return await post_repository.find_all(db)

    async def get_post(self, db: AsyncSession, post_id: int) -> Post:
        post = await post_repository.find_by_id(db, post_id)
        if post is None:
            raise NotFoundException(
                code="POST_NOT_FOUND",
                message="게시글을 찾을 수 없습니다.",
            )
        return post

    async def get_posts_by_user_id(
        self, db: AsyncSession, user_id: int
    ) -> Sequence[Post]:
        return await post_repository.find_by_user_id(db, user_id)

    async def update_post(
        self,
        db: AsyncSession,
        post_id: int,
        data: PostCreate,
        current_user: UserResponse,
    ) -> Post:
        async with db.begin():
            post = await self.get_post(db, post_id)
            if post.user_id != current_user.id:
                raise ForbiddenException(
                    code="POST_FORBIDDEN",
                    message="본인의 게시글만 수정할 수 있습니다.",
                )
            post_repository.update(db, post, data)
        return post

    async def delete_post(
        self, db: AsyncSession, post_id: int, current_user: UserResponse
    ) -> None:
        async with db.begin():
            post = await self.get_post(db, post_id)
            if post.user_id != current_user.id:
                raise ForbiddenException(
                    code="POST_FORBIDDEN",
                    message="본인의 게시글만 삭제할 수 있습니다.",
                )
            await post_repository.delete(db, post)


post_service = PostService()
