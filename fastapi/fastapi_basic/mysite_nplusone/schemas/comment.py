from pydantic import BaseModel, ConfigDict

from mysite_nplusone.schemas.user import UserResponse


class CommentResponse(BaseModel):
    id: int
    content: str

    model_config = ConfigDict(from_attributes=True)


class CommentWithUserResponse(CommentResponse):
    user: UserResponse
