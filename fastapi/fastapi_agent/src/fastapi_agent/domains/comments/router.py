from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_agent.core.database import get_db
from fastapi_agent.core.dependencies import get_current_user
from fastapi_agent.core.responses import SuccessResponse, error_responses
from fastapi_agent.domains.comments.schemas import CommentCreate, CommentResponse
from fastapi_agent.domains.comments.service import comment_service
from fastapi_agent.domains.users.schemas import UserResponse

router = APIRouter(
    prefix="/posts/{post_id}/comments", tags=["comments"], responses=error_responses(404, 422)
)


@router.post(
    "",
    response_model=SuccessResponse[CommentResponse],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(401),
)
async def create_comment(
    post_id: int,
    data: CommentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    comment = await comment_service.create_comment(db, post_id, data, current_user)
    return SuccessResponse[CommentResponse](data=comment, message="댓글이 등록되었습니다.")


@router.get("", response_model=SuccessResponse[list[CommentResponse]])
async def get_comments(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    comments = await comment_service.get_comments(db, post_id)
    return SuccessResponse[list[CommentResponse]](data=comments)


@router.get(
    "/{comment_id}",
    response_model=SuccessResponse[CommentResponse],
    responses=error_responses(404),
)
async def get_comment(
    post_id: int, comment_id: int, db: Annotated[AsyncSession, Depends(get_db)]
):
    comment = await comment_service.get_comment(db, post_id, comment_id)
    return SuccessResponse[CommentResponse](data=comment)


@router.put(
    "/{comment_id}",
    response_model=SuccessResponse[CommentResponse],
    responses=error_responses(401, 403, 404),
)
async def update_comment(
    post_id: int,
    comment_id: int,
    data: CommentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    comment = await comment_service.update_comment(db, post_id, comment_id, data, current_user)
    return SuccessResponse[CommentResponse](data=comment, message="댓글이 수정되었습니다.")


@router.delete(
    "/{comment_id}",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    responses=error_responses(401, 403, 404),
)
async def delete_comment(
    post_id: int,
    comment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    await comment_service.delete_comment(db, post_id, comment_id, current_user)
    return SuccessResponse[None](data=None, message="댓글이 삭제되었습니다.")
