from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from mysite_auth.schemas.post import PostListResponse
from mysite_auth.schemas.user import UserResponse
from mysite_auth.services.post_service import post_service

router = APIRouter(tags=["mysite_auth"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[UserResponse, Depends(get_current_user)]):
    return current_user


@router.get("/me/posts", response_model=list[PostListResponse])
def get_my_posts(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    return post_service.get_posts_by_user_id(db, current_user.id)


@router.get("/users/{user_id}/posts", response_model=list[PostListResponse])
def get_posts_by_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts_by_user_id(db, user_id)
