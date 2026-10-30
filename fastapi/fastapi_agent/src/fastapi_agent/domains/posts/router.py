from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_agent.core.database import get_db
from fastapi_agent.core.dependencies import get_current_user
from fastapi_agent.core.responses import SuccessResponse, error_responses
from fastapi_agent.domains.posts.schemas import (
    PostCreate,
    PostDetailResponse,
    PostListResponse,
)
from fastapi_agent.domains.posts.service import post_service
from fastapi_agent.domains.users.schemas import UserResponse

router = APIRouter(prefix="/posts", tags=["posts"], responses=error_responses(422))


@router.post(
    "",
    response_model=SuccessResponse[PostDetailResponse],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(401),
)
async def create_post(
    data: PostCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    post = await post_service.create_post(db, data, current_user)
    return SuccessResponse[PostDetailResponse](data=post, message="게시글이 등록되었습니다.")


@router.get("", response_model=SuccessResponse[list[PostListResponse]])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    posts = await post_service.get_posts(db)
    return SuccessResponse[list[PostListResponse]](data=posts)


@router.get(
    "/{post_id}",
    response_model=SuccessResponse[PostDetailResponse],
    responses=error_responses(404),
)
async def get_post(post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    post = await post_service.get_post(db, post_id)
    return SuccessResponse[PostDetailResponse](data=post)


@router.put(
    "/{post_id}",
    response_model=SuccessResponse[PostDetailResponse],
    responses=error_responses(401, 403, 404),
)
async def update_post(
    post_id: int,
    data: PostCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    post = await post_service.update_post(db, post_id, data, current_user)
    return SuccessResponse[PostDetailResponse](data=post, message="게시글이 수정되었습니다.")


@router.delete(
    "/{post_id}",
    response_model=SuccessResponse[None],
    status_code=status.HTTP_200_OK,
    responses=error_responses(401, 403, 404),
)
async def delete_post(
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    await post_service.delete_post(db, post_id, current_user)
    return SuccessResponse[None](data=None, message="게시글이 삭제되었습니다.")
