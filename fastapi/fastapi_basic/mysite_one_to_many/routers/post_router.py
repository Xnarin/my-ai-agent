from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from mysite_one_to_many.schemas.comment import CommentCreate, CommentResponse
from mysite_one_to_many.schemas.post import PostCreate, PostDetailResponse, PostListResponse
from mysite_one_to_many.services.comment_service import comment_service
from mysite_one_to_many.services.post_service import post_service

router = APIRouter(prefix="/posts-1n", tags=["mysite_one_to_many"])


@router.post("", response_model=PostDetailResponse, status_code=status.HTTP_201_CREATED)
def create_post(data: PostCreate, db: Annotated[Session, Depends(get_db)]):
    return post_service.create_post(db, data)


@router.get("", response_model=list[PostListResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts(db)


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
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_comment(
    post_id: int, data: CommentCreate, db: Annotated[Session, Depends(get_db)]
):
    return comment_service.create_comment(db, post_id, data)


@router.put("/{post_id}/comments/{comment_id}", response_model=CommentResponse)
def update_comment(
    post_id: int,
    comment_id: int,
    data: CommentCreate,
    db: Annotated[Session, Depends(get_db)],
):
    return comment_service.update_comment(db, post_id, comment_id, data)


@router.delete(
    "/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_comment(
    post_id: int, comment_id: int, db: Annotated[Session, Depends(get_db)]
):
    comment_service.delete_comment(db, post_id, comment_id)
