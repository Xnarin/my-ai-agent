from sqlalchemy.orm import Session

from mysite_nplusone.query_debug import collect_queries
from mysite_nplusone.repositories.post_repository import post_repository
from mysite_nplusone.schemas.post import (
    PostFullResponse,
    PostsFullResponse,
    PostsWithCommentsResponse,
    PostsWithCommentUsersResponse,
    PostsWithUserResponse,
    PostWithCommentsResponse,
    PostWithCommentUsersResponse,
    PostWithUserResponse,
)


class PostService:
    def get_posts_with_user(self, db: Session, optimized: bool = False):
        with collect_queries(db) as queries:
            posts = post_repository.find_all_with_user(db, optimized)
            data = [PostWithUserResponse.model_validate(post) for post in posts]

        return PostsWithUserResponse(
            query_count=len(queries), queries=queries, posts=data
        )

    def get_posts_with_comments(self, db: Session, optimized: bool = False):
        with collect_queries(db) as queries:
            posts = post_repository.find_all_with_comments(db, optimized)
            data = [PostWithCommentsResponse.model_validate(post) for post in posts]

        return PostsWithCommentsResponse(
            query_count=len(queries), queries=queries, posts=data
        )

    def get_posts_full(self, db: Session, optimized: bool = False):
        with collect_queries(db) as queries:
            posts = post_repository.find_all_full(db, optimized)
            data = [PostFullResponse.model_validate(post) for post in posts]

        return PostsFullResponse(query_count=len(queries), queries=queries, posts=data)

    def get_posts_with_comments_joined(self, db: Session):
        with collect_queries(db) as queries:
            posts = post_repository.find_all_with_comments_joined(db)
            data = [PostWithCommentsResponse.model_validate(post) for post in posts]

        return PostsWithCommentsResponse(
            query_count=len(queries), queries=queries, posts=data
        )

    def get_posts_with_comment_users(self, db: Session, optimized: bool = False):
        with collect_queries(db) as queries:
            posts = post_repository.find_all_with_comment_users(db, optimized)
            data = [PostWithCommentUsersResponse.model_validate(post) for post in posts]

        return PostsWithCommentUsersResponse(
            query_count=len(queries), queries=queries, posts=data
        )


post_service = PostService()
