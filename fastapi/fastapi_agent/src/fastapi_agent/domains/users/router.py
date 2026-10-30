from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_agent.core.database import get_db
from fastapi_agent.core.dependencies import get_current_user
from fastapi_agent.core.responses import SuccessResponse, error_responses
from fastapi_agent.domains.posts.schemas import PostListResponse
from fastapi_agent.domains.posts.service import post_service
from fastapi_agent.domains.users.schemas import (
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from fastapi_agent.domains.users.service import user_service

router = APIRouter(tags=["users"], responses=error_responses(422))


@router.post(
    "/auth/signup",
    response_model=SuccessResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    responses=error_responses(409),
)
async def signup(data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    user = await user_service.signup(db, data)
    return SuccessResponse[UserResponse](data=user, message="회원가입이 완료되었습니다.")


@router.post(
    "/auth/login",
    response_model=SuccessResponse[TokenResponse],
    responses=error_responses(401),
)
async def login(
    data: UserLogin, db: Annotated[AsyncSession, Depends(get_db)], response: Response
):
    access_token = await user_service.login(db, data)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return SuccessResponse[TokenResponse](data=TokenResponse(access_token=access_token))


@router.get(
    "/me", response_model=SuccessResponse[UserResponse], responses=error_responses(401)
)
async def get_me(current_user: Annotated[UserResponse, Depends(get_current_user)]):
    return SuccessResponse[UserResponse](data=current_user)


@router.get(
    "/me/posts",
    response_model=SuccessResponse[list[PostListResponse]],
    responses=error_responses(401),
)
async def get_my_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    posts = await post_service.get_posts_by_user_id(db, current_user.id)
    return SuccessResponse[list[PostListResponse]](data=posts)


@router.get("/users/{user_id}/posts", response_model=SuccessResponse[list[PostListResponse]])
async def get_posts_by_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    posts = await post_service.get_posts_by_user_id(db, user_id)
    return SuccessResponse[list[PostListResponse]](data=posts)
