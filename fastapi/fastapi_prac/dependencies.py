from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database import SessionLocal
from schemas.user import UserResponse
from services.auth_service import auth_service
from security import authentication_error

bearer_scheme = HTTPBearer(bearerFormat="JWT", auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> UserResponse:
    if credentials is None:
        raise authentication_error("로그인이 필요합니다.")
    with SessionLocal() as db:
        user = auth_service.get_current_user(db, credentials.credentials)
        return UserResponse.model_validate(user)
