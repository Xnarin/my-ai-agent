from sqlalchemy import select
from sqlalchemy.orm import Session

from mysite_many_to_many.models.post_mn import PostMN
from mysite_many_to_many.schemas.post import PostCreate


class PostRepository:
    def save(self, db: Session, new_post: PostMN):
        db.add(new_post)
        return new_post

    def find_all(self, db: Session):
        return db.scalars(select(PostMN).order_by(PostMN.id)).all()

    def find_by_id(self, db: Session, post_id: int):
        return db.get(PostMN, post_id)

    def update(self, db: Session, post: PostMN, data: PostCreate):
        post.title = data.title
        post.content = data.content
        return post

    def delete(self, db: Session, post: PostMN):
        db.delete(post)


post_repository = PostRepository()
