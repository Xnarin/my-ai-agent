from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_agent.domains.chat.models import ChatMessage, ChatRoom
from fastapi_agent.domains.chat.schemas import RoomQuery


class ChatRepository:
    async def save_room(self, db: AsyncSession, room: ChatRoom) -> ChatRoom:
        db.add(room)
        await db.flush()
        return room

    async def find_room(
        self, db: AsyncSession, room_id: str, user_id: int,
        *, lock: bool = False, include_deleted: bool = False,
    ) -> ChatRoom | None:
        statement = select(ChatRoom).where(ChatRoom.id == room_id, ChatRoom.user_id == user_id)
        if not include_deleted:
            statement = statement.where(ChatRoom.deleted_at.is_(None))
        if lock:
            statement = statement.with_for_update(nowait=True)
        return await db.scalar(statement.execution_options(populate_existing=True))

    async def find_rooms(self, db: AsyncSession, user_id: int, params: RoomQuery):
        conditions = [ChatRoom.user_id == user_id, ChatRoom.deleted_at.is_(None)]
        if params.search:
            conditions.append(ChatRoom.title.icontains(params.search, autoescape=True))
        total = await db.scalar(select(func.count()).select_from(ChatRoom).where(*conditions))
        ordering = [ChatRoom.updated_at.desc(), ChatRoom.id.desc()]
        if params.order == "asc":
            ordering = [ChatRoom.updated_at.asc(), ChatRoom.id.asc()]
        rooms = await db.scalars(
            select(ChatRoom).where(*conditions).order_by(*ordering)
            .offset(params.offset).limit(params.limit)
        )
        return rooms.all(), total

    async def find_messages(self, db: AsyncSession, room_id: str, cursor: int | None, limit: int):
        statement = select(ChatMessage).where(ChatMessage.room_id == room_id)
        if cursor is not None:
            statement = statement.where(ChatMessage.id < cursor)
        result = await db.scalars(statement.order_by(ChatMessage.id.desc()).limit(limit + 1))
        return result.all()

    async def save_messages(self, db: AsyncSession, messages: list[ChatMessage]) -> None:
        db.add_all(messages)
        await db.flush()

    async def delete_room(self, db: AsyncSession, room: ChatRoom) -> None:
        await db.execute(delete(ChatMessage).where(ChatMessage.room_id == room.id))
        await db.delete(room)


chat_repository = ChatRepository()
