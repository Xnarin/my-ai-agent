from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from mysite_one_to_many.models.comment_1n import Comment1N
from mysite_one_to_many.repositories.comment_repository import comment_repository
from mysite_one_to_many.schemas.comment import CommentCreate
from mysite_one_to_many.services.post_service import post_service


class CommentService:
    def create_comment(self, db: Session, post_id: int, data: CommentCreate):
        with db.begin():
            post = post_service.get_post(db, post_id)
            new_comment = Comment1N(content=data.content, post=post)
            comment_repository.save(db, new_comment)

        return new_comment

    def update_comment(
        self, db: Session, post_id: int, comment_id: int, data: CommentCreate
    ):
        with db.begin():
            comment = self._get_verified_comment(db, post_id, comment_id)
            updated_comment = comment_repository.update(db, comment, data)

        return updated_comment

    def delete_comment(self, db: Session, post_id: int, comment_id: int):
        with db.begin():
            comment = self._get_verified_comment(db, post_id, comment_id)
            comment_repository.delete(db, comment)

    def _get_verified_comment(self, db: Session, post_id: int, comment_id: int):
        comment = comment_repository.find_by_id(db, comment_id)
        if comment is None or comment.post_id != post_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 게시글의 댓글을 찾을 수 없습니다.",
            )
        return comment


comment_service = CommentService()
