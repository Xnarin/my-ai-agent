from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from mysite_many_to_many.schemas.post import (
    PostCreate,
    PostCreateWithTags,
    PostDetailResponse,
    PostListResponse,
)
from mysite_many_to_many.schemas.tag import TagCreate
from mysite_many_to_many.services.post_service import post_service

router = APIRouter(prefix="/posts-mn", tags=["mysite_many_to_many"])


@router.post("", response_model=PostDetailResponse, status_code=status.HTTP_201_CREATED)
def create_post(data: PostCreate, db: Annotated[Session, Depends(get_db)]):
    return post_service.create_post(db, data)


@router.get("", response_model=list[PostListResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts(db)


@router.post(
    "/with-tags",
    response_model=PostDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_post_with_tags(
    data: PostCreateWithTags, db: Annotated[Session, Depends(get_db)]
):
    return post_service.create_post_with_tags(db, data)


@router.get("/{post_id}", response_model=PostDetailResponse)
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    return post_service.get_post(db, post_id)


@router.put("/{post_id}", response_model=PostDetailResponse)
def update_post(
    post_id: int, data: PostCreate, db: Annotated[Session, Depends(get_db)]
):
    return post_service.update_post(db, post_id, data)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    post_service.delete_post(db, post_id)


@router.post(
    "/{post_id}/tags",
    response_model=PostDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_tag_to_post(
    post_id: int, data: TagCreate, db: Annotated[Session, Depends(get_db)]
):
    return post_service.add_tag_to_post(db, post_id, data)


@router.delete("/{post_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tag_from_post(
    post_id: int, tag_id: int, db: Annotated[Session, Depends(get_db)]
):
    post_service.remove_tag_from_post(db, post_id, tag_id)
