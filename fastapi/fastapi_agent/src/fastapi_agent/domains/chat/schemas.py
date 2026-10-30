from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RagChatRequest(BaseModel):
    question: str = Field(min_length=1)


class RoomCreate(BaseModel):
    title: str = Field(default="새 채팅", min_length=1, max_length=100)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RoomUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RoomQuery(BaseModel):
    search: str = Field(default="", max_length=100)
    order: Literal["asc", "desc"] = "desc"
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class RoomResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoomPageResponse(BaseModel):
    items: list[RoomResponse]
    total: int


class MessageCreate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class MessageQuery(BaseModel):
    cursor: int | None = Field(default=None, gt=0)
    limit: int = Field(default=30, ge=1, le=100)

    model_config = ConfigDict(extra="forbid")


class MessageResponse(BaseModel):
    id: int
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MessagePageResponse(BaseModel):
    items: list[MessageResponse]
    next_cursor: int | None
    has_more: bool


class TurnResponse(BaseModel):
    user_message: MessageResponse
    assistant_message: MessageResponse
