from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_agent.domains.users.models import User


class UserRepository:
    async def save(self, db: AsyncSession, user: User) -> User:
        db.add(user)
        await db.flush()
        return user

    async def find_by_email(self, db: AsyncSession, email: str) -> User | None:
        return await db.scalar(select(User).where(User.email == email))

    async def find_by_id(self, db: AsyncSession, user_id: int) -> User | None:
        return await db.get(User, user_id)


user_repository = UserRepository()
