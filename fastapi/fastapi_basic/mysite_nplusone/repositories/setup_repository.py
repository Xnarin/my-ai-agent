from sqlalchemy import delete
from sqlalchemy.orm import Session

from mysite_nplusone.models import CommentNPlusOne, PostNPlusOne, UserNPlusOne


class SetupRepository:
    def clear(self, db: Session):
        db.execute(delete(CommentNPlusOne))
        db.execute(delete(PostNPlusOne))
        db.execute(delete(UserNPlusOne))

    def save_users(self, db: Session, users: list[UserNPlusOne]):
        db.add_all(users)


setup_repository = SetupRepository()
