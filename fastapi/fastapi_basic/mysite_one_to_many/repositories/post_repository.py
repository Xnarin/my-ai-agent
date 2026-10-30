from sqlalchemy import select
from sqlalchemy.orm import Session

from mysite_one_to_many.models.post_1n import Post1N
from mysite_one_to_many.schemas.post import PostCreate


class PostRepository:
    def save(self, db: Session, new_post: Post1N):
        db.add(new_post)
        return new_post

    def find_all(self, db: Session):
        return db.scalars(select(Post1N).order_by(Post1N.id)).all()

    def find_by_id(self, db: Session, id: int):
        return db.get(Post1N, id)

    def update(self, db: Session, post: Post1N, data: PostCreate):
        post.title = data.title
        post.content = data.content
        return post

    def delete(self, db: Session, post: Post1N):
        db.delete(post)


post_repository = PostRepository()
