from sqlalchemy.orm import Session

from mysite_one_to_many.models.comment_1n import Comment1N
from mysite_one_to_many.schemas.comment import CommentCreate


class CommentRepository:
    def save(self, db: Session, new_comment: Comment1N):
        db.add(new_comment)
        return new_comment

    def find_by_id(self, db: Session, comment_id: int):
        return db.get(Comment1N, comment_id)

    def update(self, db: Session, comment: Comment1N, data: CommentCreate):
        comment.content = data.content
        return comment

    def delete(self, db: Session, comment: Comment1N):
        db.delete(comment)


comment_repository = CommentRepository()
