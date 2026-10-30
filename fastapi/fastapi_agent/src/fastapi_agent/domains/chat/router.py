import json
import logging
from contextlib import aclosing
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_agent.core.database import get_db
from fastapi_agent.core.dependencies import get_current_user
from fastapi_agent.core.responses import SuccessResponse, error_responses
from fastapi_agent.domains.chat.rag_service import rag_chat_service
from fastapi_agent.domains.chat.schemas import (
    MessageCreate, MessagePageResponse, MessageQuery, RagChatRequest,
    RoomCreate, RoomPageResponse, RoomQuery, RoomResponse, RoomUpdate, TurnResponse,
)
from fastapi_agent.domains.chat.service import ChatService
from fastapi_agent.domains.users.schemas import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    dependencies=[Depends(get_current_user)],
    responses=error_responses(401, 422),
)


def get_chat_service(request: Request) -> ChatService:
    return ChatService(request.app.state.chat_agent)


Database = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[UserResponse, Depends(get_current_user)]
Chat = Annotated[ChatService, Depends(get_chat_service)]


def format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post(
    "/rag/stream",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def stream_rag(
    data: RagChatRequest,
    request: Request,
):
    agent = request.app.state.rag_agent

    async def events():
        try:
            async for event, payload in rag_chat_service.stream_rag(agent, data.question):
                yield format_sse(event, payload)
        except Exception:
            logger.exception("RAG 스트리밍 실행 실패")
            yield format_sse("error", {"message": "답변 생성 중 오류가 발생했습니다."})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/rooms", status_code=201, response_model=SuccessResponse[RoomResponse])
async def create_room(data: RoomCreate, db: Database, user: CurrentUser, service: Chat):
    return SuccessResponse(data=await service.create_room(db, user.id, data.title))


@router.get("/rooms", response_model=SuccessResponse[RoomPageResponse])
async def get_rooms(params: Annotated[RoomQuery, Query()], db: Database, user: CurrentUser, service: Chat):
    return SuccessResponse(data=await service.get_rooms(db, user.id, params))


@router.get("/rooms/{room_id}", response_model=SuccessResponse[RoomResponse], responses=error_responses(404))
async def get_room(room_id: str, db: Database, user: CurrentUser, service: Chat):
    return SuccessResponse(data=await service.get_room(db, room_id, user.id))


@router.patch("/rooms/{room_id}", response_model=SuccessResponse[RoomResponse], responses=error_responses(404, 409))
async def rename_room(room_id: str, data: RoomUpdate, db: Database, user: CurrentUser, service: Chat):
    return SuccessResponse(data=await service.rename_room(db, room_id, user.id, data.title))


@router.delete("/rooms/{room_id}", response_model=SuccessResponse[None], responses=error_responses(404, 409))
async def delete_room(room_id: str, db: Database, user: CurrentUser, service: Chat):
    await service.delete_room(db, room_id, user.id)
    return SuccessResponse(data=None, message="채팅방이 삭제되었습니다.")


@router.get("/rooms/{room_id}/messages", response_model=SuccessResponse[MessagePageResponse], responses=error_responses(404))
async def get_messages(room_id: str, params: Annotated[MessageQuery, Query()], db: Database, user: CurrentUser, service: Chat):
    return SuccessResponse(data=await service.get_messages(db, room_id, user.id, params))


@router.post("/rooms/{room_id}/messages", response_model=SuccessResponse[TurnResponse], responses=error_responses(404, 409))
async def send_message(room_id: str, data: MessageCreate, db: Database, user: CurrentUser, service: Chat):
    return SuccessResponse(data=await service.send_message(db, room_id, user.id, data.content))


@router.post(
    "/rooms/{room_id}/messages/stream", response_class=StreamingResponse,
    responses={**error_responses(404, 409), 200: {"content": {"text/event-stream": {}}}},
)
async def stream_message(room_id: str, data: MessageCreate, db: Database, user: CurrentUser, service: Chat):
    turn = service.run_turn(db, room_id, user.id, data.content)
    # 스트리밍 헤더를 보내기 전에 소유권과 실행 가능 여부를 확인한다.
    first_event, first_payload = await anext(turn)

    async def events():
        async with aclosing(turn):
            try:
                yield format_sse(first_event, first_payload)
                async for event, payload in turn:
                    yield format_sse(event, payload)
            except Exception:
                logger.exception("챗봇 실행 실패")
                yield format_sse("error", {"message": "답변 생성 중 오류가 발생했습니다."})

    return StreamingResponse(
        events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
