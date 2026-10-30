from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from mysite_db.schemas.post import PostCreate, PostDetailResponse, PostListResponse
from mysite_db.services.post_service import post_service

router = APIRouter(prefix="/posts-db", tags=["mysite_db"])


@router.post("", response_model=PostDetailResponse, status_code=status.HTTP_201_CREATED)
def create_post(data: PostCreate, db: Annotated[Session, Depends(get_db)]):
    return post_service.create_post(db, data)


@router.get("", response_model=list[PostListResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts(db)


@router.get("/{id}", response_model=PostDetailResponse)
def get_post(id: int, db: Annotated[Session, Depends(get_db)]):
    return post_service.get_post(db, id)


@router.put("/{id}", response_model=PostDetailResponse)
def update_post(id: int, data: PostCreate, db: Annotated[Session, Depends(get_db)]):
    return post_service.update_post(db, id, data)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(id: int, db: Annotated[Session, Depends(get_db)]):
    post_service.delete_post(db, id)
