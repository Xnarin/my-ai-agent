from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class Post2Query(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    keyword: str | None = Field(default=None, min_length=1, max_length=100)
    category: Literal["backend", "frontend", "ai"] | None = None
    min_views: int | None = Field(default=None, ge=0)
    sort_by: Literal["id", "title", "created_at", "views"] = "created_at"
    order: Literal["asc", "desc"] = "desc"

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Post2Response(BaseModel):
    id: int
    title: str
    content: str
    category: str
    views: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Post2PageResponse(BaseModel):
    items: list[Post2Response]
    total: int
    page: int
    size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class Post2SetupResponse(BaseModel):
    count: int
