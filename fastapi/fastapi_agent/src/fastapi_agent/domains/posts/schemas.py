from pydantic import BaseModel, ConfigDict, Field

from fastapi_agent.domains.comments.schemas import CommentResponse
from fastapi_agent.domains.users.schemas import UserResponse


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1)


class PostListResponse(BaseModel):
    id: int
    title: str
    user: UserResponse

    model_config = ConfigDict(from_attributes=True)


class PostDetailResponse(BaseModel):
    id: int
    title: str
    content: str
    user: UserResponse
    comments: list[CommentResponse]

    model_config = ConfigDict(from_attributes=True)
