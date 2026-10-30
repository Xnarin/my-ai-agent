from collections.abc import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_agent.core.exceptions import ForbiddenException, NotFoundException
from fastapi_agent.domains.comments.models import Comment
from fastapi_agent.domains.comments.repository import comment_repository
from fastapi_agent.domains.comments.schemas import CommentCreate
from fastapi_agent.domains.posts.repository import post_repository
from fastapi_agent.domains.users.schemas import UserResponse


class CommentService:
    async def require_post(self, db: AsyncSession, post_id: int) -> None:
        if not await post_repository.exists_by_id(db, post_id):
            raise NotFoundException(
                code="POST_NOT_FOUND",
                message="게시글을 찾을 수 없습니다.",
            )

    async def create_comment(
        self,
        db: AsyncSession,
        post_id: int,
        data: CommentCreate,
        current_user: UserResponse,
    ) -> Comment:
        async with db.begin():
            await self.require_post(db, post_id)
            comment = Comment(
                content=data.content, post_id=post_id, user_id=current_user.id
            )
            await comment_repository.save(db, comment)
        return comment

    async def get_comments(self, db: AsyncSession, post_id: int) -> Sequence[Comment]:
        await self.require_post(db, post_id)
        return await comment_repository.find_by_post_id(db, post_id)

    async def get_comment(
        self, db: AsyncSession, post_id: int, comment_id: int
    ) -> Comment:
        comment = await comment_repository.find_by_id(db, post_id, comment_id)
        if comment is None:
            raise NotFoundException(
                code="COMMENT_NOT_FOUND",
                message="댓글을 찾을 수 없습니다.",
            )
        return comment

    async def update_comment(
        self,
        db: AsyncSession,
        post_id: int,
        comment_id: int,
        data: CommentCreate,
        current_user: UserResponse,
    ) -> Comment:
        async with db.begin():
            comment = await self.get_comment(db, post_id, comment_id)
            if comment.user_id != current_user.id:
                raise ForbiddenException(
                    code="COMMENT_FORBIDDEN",
                    message="본인의 댓글만 수정할 수 있습니다.",
                )
            comment_repository.update(db, comment, data)
        return comment

    async def delete_comment(
        self,
        db: AsyncSession,
        post_id: int,
        comment_id: int,
        current_user: UserResponse,
    ) -> None:
        async with db.begin():
            comment = await self.get_comment(db, post_id, comment_id)
            if comment.user_id != current_user.id:
                raise ForbiddenException(
                    code="COMMENT_FORBIDDEN",
                    message="본인의 댓글만 삭제할 수 있습니다.",
                )
            await comment_repository.delete(db, comment)


comment_service = CommentService()
