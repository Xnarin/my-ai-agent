from pydantic import BaseModel, ConfigDict

from mysite_nplusone.schemas.comment import CommentResponse, CommentWithUserResponse
from mysite_nplusone.schemas.user import UserResponse


class PostResponse(BaseModel):
    id: int
    title: str
    user_id: int

    model_config = ConfigDict(from_attributes=True)


class PostWithUserResponse(PostResponse):
    user: UserResponse


class PostWithCommentsResponse(PostResponse):
    comments: list[CommentResponse]


class PostWithCommentUsersResponse(PostResponse):
    comments: list[CommentWithUserResponse]


class PostFullResponse(PostResponse):
    user: UserResponse
    comments: list[CommentResponse]


class QueryResponse(BaseModel):
    query_count: int
    queries: list[str]


class PostsWithUserResponse(QueryResponse):
    posts: list[PostWithUserResponse]


class PostsWithCommentsResponse(QueryResponse):
    posts: list[PostWithCommentsResponse]


class PostsWithCommentUsersResponse(QueryResponse):
    posts: list[PostWithCommentUsersResponse]


class PostsFullResponse(QueryResponse):
    posts: list[PostFullResponse]
