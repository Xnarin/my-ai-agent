from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.user import User
from repositories.user_repository import user_repository
from schemas.user import UserCreate, UserLogin
from security import (
    authentication_error,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class AuthService:
    def signup(self, db: Session, data: UserCreate) -> User:
        email = str(data.email).lower()
        hashed_password = hash_password(data.password)

        with db.begin():
            if user_repository.find_by_email(db, email) is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="이미 등록된 이메일입니다.",
                )
            user = User(email=email, hashed_password=hashed_password)
            user_repository.save(db, user)

        return user

    def login(self, db: Session, data: UserLogin) -> str:
        email = str(data.email).lower()
        with db.begin():
            user = user_repository.find_by_email(db, email)
            if user is None or not verify_password(data.password, user.hashed_password):
                raise authentication_error("이메일 또는 비밀번호가 올바르지 않습니다.")

            user_id = user.id

        return create_access_token(user_id)

    def get_current_user(self, db: Session, token: str) -> User:
        user_id = decode_access_token(token)
        user = user_repository.find_by_id(db, user_id)
        if user is None:
            raise authentication_error()
        return user


auth_service = AuthService()
