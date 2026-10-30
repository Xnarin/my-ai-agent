from pydantic import BaseModel, ConfigDict, Field

from mysite_one_to_many.schemas.comment import CommentResponse


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1)


class PostDetailResponse(BaseModel):
    id: int
    title: str
    content: str
    comments: list[CommentResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PostListResponse(BaseModel):
    id: int
    title: str

    model_config = ConfigDict(from_attributes=True)
