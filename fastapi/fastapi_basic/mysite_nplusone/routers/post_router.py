from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from mysite_nplusone.schemas.post import (
    PostsFullResponse,
    PostsWithCommentsResponse,
    PostsWithCommentUsersResponse,
    PostsWithUserResponse,
)
from mysite_nplusone.schemas.setup import SetupResponse
from mysite_nplusone.services.post_service import post_service
from mysite_nplusone.services.setup_service import setup_service

router = APIRouter(prefix="/nplusone", tags=["mysite_nplusone"])


@router.post("/setup", response_model=SetupResponse, summary="실습 데이터 초기화")
def setup(db: Annotated[Session, Depends(get_db)]):
    return setup_service.setup(db)


@router.get(
    "/posts/with-user",
    response_model=PostsWithUserResponse,
    summary="게시글과 작성자: 지연 로딩",
)
def get_posts_with_user(db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts_with_user(db)


@router.get(
    "/posts/with-user/optimized",
    response_model=PostsWithUserResponse,
    summary="게시글과 작성자: joinedload",
)
def get_posts_with_user_optimized(db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts_with_user(db, optimized=True)


@router.get(
    "/posts/with-comments",
    response_model=PostsWithCommentsResponse,
    summary="게시글과 댓글: 지연 로딩",
)
def get_posts_with_comments(db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts_with_comments(db)


@router.get(
    "/posts/with-comments/optimized",
    response_model=PostsWithCommentsResponse,
    summary="게시글과 댓글: selectinload",
)
def get_posts_with_comments_optimized(db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts_with_comments(db, optimized=True)


@router.get(
    "/posts/with-comments/joined",
    response_model=PostsWithCommentsResponse,
    summary="게시글과 댓글: joinedload + unique",
)
def get_posts_with_comments_joined(db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts_with_comments_joined(db)


@router.get(
    "/posts/full",
    response_model=PostsFullResponse,
    summary="게시글과 작성자·댓글: 지연 로딩",
)
def get_posts_full(db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts_full(db)


@router.get(
    "/posts/full/optimized",
    response_model=PostsFullResponse,
    summary="게시글과 작성자·댓글: joinedload + selectinload",
)
def get_posts_full_optimized(db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts_full(db, optimized=True)


@router.get(
    "/posts/with-comment-users",
    response_model=PostsWithCommentUsersResponse,
    summary="게시글과 댓글 작성자: 지연 로딩",
)
def get_posts_with_comment_users(db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts_with_comment_users(db)


@router.get(
    "/posts/with-comment-users/optimized",
    response_model=PostsWithCommentUsersResponse,
    summary="게시글과 댓글 작성자: selectinload → joinedload",
)
def get_posts_with_comment_users_optimized(db: Annotated[Session, Depends(get_db)]):
    return post_service.get_posts_with_comment_users(db, optimized=True)
