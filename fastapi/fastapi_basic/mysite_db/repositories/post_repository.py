from sqlalchemy import select
from sqlalchemy.orm import Session

from mysite_db.models.post import Post
from mysite_db.schemas.post import PostCreate


class PostRepository:
    def save(self, db: Session, new_post: Post):
        db.add(new_post)
        return new_post

    def find_all(self, db: Session):
        return db.scalars(select(Post).order_by(Post.id)).all()

    def find_by_id(self, db: Session, id: int):
        return db.get(Post, id)

    def update(self, db: Session, post: Post, data: PostCreate):
        post.title = data.title
        post.content = data.content
        return post

    def delete(self, db: Session, post: Post):
        db.delete(post)


post_repository = PostRepository()
