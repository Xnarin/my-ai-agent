from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from mysite_auth.models.post import PostAuth
from mysite_auth.repositories.post_repository import post_repository
from mysite_auth.schemas.post import PostCreate
from mysite_auth.schemas.user import UserResponse


class PostService:
    def create_post(self, db: Session, data: PostCreate, current_user: UserResponse):
        with db.begin():
            new_post = PostAuth(
                title=data.title, content=data.content, user_id=current_user.id
            )
            post_repository.save(db, new_post)
        return new_post

    def get_posts(self, db: Session):
        return post_repository.find_all(db)

    def get_post(self, db: Session, post_id: int):
        post = post_repository.find_by_id(db, post_id)
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다.",
            )
        return post

    def get_posts_by_user_id(self, db: Session, user_id: int):
        return post_repository.find_by_user_id(db, user_id)

    def update_post(
        self, db: Session, post_id: int, data: PostCreate, current_user: UserResponse
    ):
        with db.begin():
            post = self.get_post(db, post_id)
            if post.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="본인의 게시글만 수정할 수 있습니다.",
                )
            updated_post = post_repository.update(db, post, data)
        return updated_post

    def delete_post(self, db: Session, post_id: int, current_user: UserResponse):
        with db.begin():
            post = self.get_post(db, post_id)
            if post.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="본인의 게시글만 삭제할 수 있습니다.",
                )
            post_repository.delete(db, post)


post_service = PostService()
