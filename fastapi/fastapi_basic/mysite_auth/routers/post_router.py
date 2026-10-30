from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from mysite_auth.schemas.post import PostCreate, PostDetailResponse, PostListResponse
from mysite_auth.schemas.user import UserResponse
from mysite_auth.services.post_service import post_service

router = APIRouter(prefix="/posts-auth", tags=["mysite_auth"])


@router.post("", response_model=PostDetailResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    data: PostCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    return post_service.create_post(db, data, current_user)


@router.get("", response_model=list[PostListResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts(db)


@router.get("/{post_id}", response_model=PostDetailResponse)
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    return post_service.get_post(db, post_id)


@router.put("/{post_id}", response_model=PostDetailResponse)
def update_post(
    post_id: int,
    data: PostCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    return post_service.update_post(db, post_id, data, current_user)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    post_service.delete_post(db, post_id, current_user)
