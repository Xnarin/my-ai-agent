from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from mysite_nplusone.models import CommentNPlusOne, PostNPlusOne


class PostRepository:
    def find_all_with_user(self, db: Session, optimized: bool = False):
        stmt = select(PostNPlusOne).order_by(PostNPlusOne.id)
        if optimized:
            stmt = stmt.options(joinedload(PostNPlusOne.user))
        return db.scalars(stmt).all()

    def find_all_with_comments(self, db: Session, optimized: bool = False):
        stmt = select(PostNPlusOne).order_by(PostNPlusOne.id)
        if optimized:
            stmt = stmt.options(selectinload(PostNPlusOne.comments))
        return db.scalars(stmt).all()

    def find_all_full(self, db: Session, optimized: bool = False):
        stmt = select(PostNPlusOne).order_by(PostNPlusOne.id)
        if optimized:
            stmt = stmt.options(
                joinedload(PostNPlusOne.user),
                selectinload(PostNPlusOne.comments),
            )
        return db.scalars(stmt).all()

    def find_all_with_comments_joined(self, db: Session):
        stmt = (
            select(PostNPlusOne)
            .options(joinedload(PostNPlusOne.comments))
            .order_by(PostNPlusOne.id)
        )
        return db.scalars(stmt).unique().all()

    def find_all_with_comment_users(self, db: Session, optimized: bool = False):
        stmt = select(PostNPlusOne).order_by(PostNPlusOne.id)
        if optimized:
            stmt = stmt.options(
                selectinload(PostNPlusOne.comments).joinedload(CommentNPlusOne.user)
            )
        return db.scalars(stmt).all()


post_repository = PostRepository()
