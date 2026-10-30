from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from mysite_auth.models.post import PostAuth
from mysite_auth.schemas.post import PostCreate


class PostRepository:
    def save(self, db: Session, new_post: PostAuth):
        db.add(new_post)
        return new_post

    def find_all(self, db: Session):
        return db.scalars(
            select(PostAuth).options(joinedload(PostAuth.user)).order_by(PostAuth.id)
        ).all()

    def find_by_id(self, db: Session, post_id: int):
        return db.scalar(
            select(PostAuth)
            .options(joinedload(PostAuth.user))
            .where(PostAuth.id == post_id)
        )

    def find_by_user_id(self, db: Session, user_id: int):
        return db.scalars(
            select(PostAuth)
            .options(joinedload(PostAuth.user))
            .where(PostAuth.user_id == user_id)
            .order_by(PostAuth.id)
        ).all()

    def update(self, db: Session, post: PostAuth, data: PostCreate):
        post.title = data.title
        post.content = data.content
        return post

    def delete(self, db: Session, post: PostAuth):
        db.delete(post)


post_repository = PostRepository()
