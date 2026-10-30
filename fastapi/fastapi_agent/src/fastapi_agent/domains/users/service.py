from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from fastapi_agent.core.exceptions import ConflictException, UnauthorizedException
from fastapi_agent.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from fastapi_agent.domains.users.models import User
from fastapi_agent.domains.users.repository import user_repository
from fastapi_agent.domains.users.schemas import UserCreate, UserLogin


class UserService:
    async def signup(self, db: AsyncSession, data: UserCreate) -> User:
        email = str(data.email).lower()
        hashed_password = await run_in_threadpool(hash_password, data.password)

        async with db.begin():
            if await user_repository.find_by_email(db, email) is not None:
                raise ConflictException(
                    code="EMAIL_ALREADY_EXISTS",
                    message="이미 등록된 이메일입니다.",
                )
            user = User(email=email, hashed_password=hashed_password)
            await user_repository.save(db, user)

        return user

    async def login(self, db: AsyncSession, data: UserLogin) -> str:
        email = str(data.email).lower()
        async with db.begin():
            user = await user_repository.find_by_email(db, email)
            if user is None or not await run_in_threadpool(
                verify_password, data.password, user.hashed_password
            ):
                raise UnauthorizedException(
                    message="이메일 또는 비밀번호가 올바르지 않습니다.", code="INVALID_CREDENTIALS"
                )

            user_id = user.id

        return create_access_token(user_id)

    async def get_current_user(self, db: AsyncSession, token: str) -> User:
        user_id = decode_access_token(token)
        user = await user_repository.find_by_id(db, user_id)
        if user is None:
            raise UnauthorizedException(
                message="유효하지 않거나 만료된 토큰입니다.", code="INVALID_TOKEN"
            )
        return user


user_service = UserService()
