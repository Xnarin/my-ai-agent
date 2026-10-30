from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from fastapi_agent.domains.users.schemas import UserResponse


class CommentCreate(BaseModel):
    content: str = Field(min_length=1)


class CommentResponse(BaseModel):
    id: int
    content: str
    post_id: int
    user: UserResponse
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
