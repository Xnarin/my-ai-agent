from sqlalchemy import select
from sqlalchemy.orm import Session

from mysite_auth.models.user import User


class UserRepository:
    def save(self, db: Session, user: User) -> User:
        db.add(user)
        return user

    def find_by_email(self, db: Session, email: str) -> User | None:
        return db.scalar(select(User).where(User.email == email))

    def find_by_id(self, db: Session, user_id: int) -> User | None:
        return db.get(User, user_id)


user_repository = UserRepository()
