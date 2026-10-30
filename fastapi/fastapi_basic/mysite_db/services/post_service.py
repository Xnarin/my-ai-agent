from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from mysite_db.models.post import Post
from mysite_db.repositories.post_repository import post_repository
from mysite_db.schemas.post import PostCreate


class PostService:
    def create_post(self, db: Session, data: PostCreate):
        with db.begin():
            new_post = Post(title=data.title, content=data.content)
            post_repository.save(db, new_post)

        return new_post

    def get_posts(self, db: Session):
        return post_repository.find_all(db)

    def get_post(self, db: Session, id: int):
        post = post_repository.find_by_id(db, id)
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다.",
            )
        return post

    def update_post(self, db: Session, id: int, data: PostCreate):
        with db.begin():
            post = self.get_post(db, id)
            updated_post = post_repository.update(db, post, data)

        return updated_post

    def delete_post(self, db: Session, id: int):
        with db.begin():
            post = self.get_post(db, id)
            post_repository.delete(db, post)


post_service = PostService()
