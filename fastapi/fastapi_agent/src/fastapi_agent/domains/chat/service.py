from contextlib import aclosing
from datetime import datetime, timezone
from uuid import uuid4

from langchain_core.messages import AIMessage
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_agent.core.exceptions import ConflictException, NotFoundException
from fastapi_agent.domains.chat.models import ChatMessage, ChatRoom
from fastapi_agent.domains.chat.repository import chat_repository
from fastapi_agent.domains.chat.schemas import (
    MessagePageResponse, MessageQuery, MessageResponse, RoomPageResponse,
    RoomQuery, RoomResponse, TurnResponse,
)


TOOL_LABELS = {
    "search_weather": "날씨 조회",
    "get_movie_list": "영화 목록 조회",
    "get_movie_detail": "영화 상세 조회",
}


class ChatService:
    def __init__(self, agent: CompiledStateGraph):
        self.agent = agent

    async def _owned_room(self, db, room_id, user_id, *, lock=False, include_deleted=False):
        try:
            room = await chat_repository.find_room(
                db, room_id, user_id, lock=lock, include_deleted=include_deleted
            )
        except DBAPIError as exc:
            if getattr(exc.orig, "sqlstate", None) == "55P03":
                raise ConflictException(
                    code="CHAT_ROOM_BUSY", message="이 채팅방의 요청을 처리 중입니다. 잠시 후 다시 시도해 주세요."
                ) from exc
            raise
        if room is None:
            raise NotFoundException(code="CHAT_ROOM_NOT_FOUND", message="채팅방을 찾을 수 없습니다.")
        return room

    async def create_room(self, db: AsyncSession, user_id: int, title: str) -> RoomResponse:
        room = ChatRoom(id=str(uuid4()), user_id=user_id, title=title)
        config = await self.agent.aupdate_state(
            {"configurable": {"thread_id": room.thread_id}}, {"messages": []}
        )
        room.checkpoint_id = config["configurable"]["checkpoint_id"]
        try:
            async with db.begin():
                await chat_repository.save_room(db, room)
                response = RoomResponse.model_validate(room)
        except BaseException:
            await self.agent.checkpointer.adelete_thread(room.thread_id)
            raise
        return response

    async def get_rooms(self, db: AsyncSession, user_id: int, params: RoomQuery):
        async with db.begin():
            rooms, total = await chat_repository.find_rooms(db, user_id, params)
            return RoomPageResponse(items=[RoomResponse.model_validate(r) for r in rooms], total=total)

    async def get_room(self, db: AsyncSession, room_id: str, user_id: int):
        async with db.begin():
            room = await self._owned_room(db, room_id, user_id)
            return RoomResponse.model_validate(room)

    async def rename_room(self, db: AsyncSession, room_id: str, user_id: int, title: str):
        async with db.begin():
            room = await self._owned_room(db, room_id, user_id, lock=True)
            room.title = title
            room.updated_at = datetime.now(timezone.utc)
            return RoomResponse.model_validate(room)

    async def delete_room(self, db: AsyncSession, room_id: str, user_id: int):
        # 삭제 표시를 먼저 확정해 체크포인트 정리 중 새 실행을 막는다.
        async with db.begin():
            room = await self._owned_room(db, room_id, user_id, lock=True, include_deleted=True)
            room.deleted_at = datetime.now(timezone.utc)
        async with db.begin():
            room = await self._owned_room(db, room_id, user_id, lock=True, include_deleted=True)
            await self.agent.checkpointer.adelete_thread(room.thread_id)
            await chat_repository.delete_room(db, room)

    async def get_messages(self, db: AsyncSession, room_id: str, user_id: int, params: MessageQuery):
        async with db.begin():
            await self._owned_room(db, room_id, user_id)
            rows = await chat_repository.find_messages(db, room_id, params.cursor, params.limit)
            has_more = len(rows) > params.limit
            page = rows[:params.limit]
            return MessagePageResponse(
                items=[MessageResponse.model_validate(m) for m in reversed(page)],
                next_cursor=page[-1].id if has_more else None,
                has_more=has_more,
            )

    async def send_message(self, db: AsyncSession, room_id: str, user_id: int, content: str):
        async with aclosing(self.run_turn(db, room_id, user_id, content, stream=False)) as events:
            async for event, payload in events:
                if event == "done":
                    return TurnResponse.model_validate(payload)

    async def run_turn(
        self, db: AsyncSession, room_id: str, user_id: int, content: str, *, stream: bool = True,
    ):
        async with db.begin():
            room = await self._owned_room(db, room_id, user_id, lock=True)
            config = {"configurable": {
                "thread_id": room.thread_id, "checkpoint_id": room.checkpoint_id,
            }}
            inputs = {"messages": [{"role": "user", "content": content}]}
            yield "status", {"message": "답변을 생성하고 있습니다."}

            if stream:
                result = None
                active_tools = {}
                try:
                    async with aclosing(self.agent.astream_events(
                        inputs, config=config, version="v2"
                    )) as events:
                        async for event in events:
                            kind = event["event"]
                            data = event["data"]
                            if kind == "on_chat_model_start":
                                yield "status", {"message": "답변을 생성하고 있습니다."}
                            elif kind == "on_chat_model_stream":
                                chunk = data["chunk"]
                                if isinstance(chunk, AIMessage) and chunk.text:
                                    yield "token", {"content": chunk.text}
                            elif kind == "on_tool_start":
                                tool = {
                                    "id": event["run_id"],
                                    "name": event["name"],
                                    "label": TOOL_LABELS.get(event["name"], "정보 조회"),
                                }
                                active_tools[tool["id"]] = tool
                                yield "tool_start", tool
                            elif kind == "on_tool_end":
                                tool = active_tools.pop(event["run_id"], None)
                                if tool is not None:
                                    failed = getattr(data.get("output"), "status", None) == "error"
                                    yield "tool_error" if failed else "tool_end", tool
                            elif kind == "on_chain_end" and not event["parent_ids"]:
                                result = data["output"]
                except Exception:
                    for tool in active_tools.values():
                        yield "tool_error", tool
                    raise
            else:
                result = await self.agent.ainvoke(inputs, config=config)

            final = result["messages"][-1] if result and result.get("messages") else None
            if not isinstance(final, AIMessage) or final.tool_calls or not final.text.strip():
                raise RuntimeError("Agent가 최종 답변을 반환하지 않았습니다.")

            state = await self.agent.aget_state({"configurable": {"thread_id": room.thread_id}})
            if state.next:
                raise RuntimeError("Agent 실행이 완료되지 않았습니다.")
            user_message = ChatMessage(room_id=room.id, role="user", content=content)
            assistant_message = ChatMessage(room_id=room.id, role="assistant", content=final.text)
            await chat_repository.save_messages(db, [user_message, assistant_message])
            # 화면 기록과 함께 확정한 체크포인트에서 다음 대화를 시작한다.
            room.checkpoint_id = state.config["configurable"]["checkpoint_id"]
            room.updated_at = datetime.now(timezone.utc)
            response = TurnResponse(
                user_message=MessageResponse.model_validate(user_message),
                assistant_message=MessageResponse.model_validate(assistant_message),
            )
        yield "done", response.model_dump(mode="json")
