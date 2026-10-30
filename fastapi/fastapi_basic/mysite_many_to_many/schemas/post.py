from pydantic import BaseModel, ConfigDict, Field

from mysite_many_to_many.schemas.tag import TagResponse


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=50)
    content: str = Field(min_length=1)


class PostCreateWithTags(PostCreate):
    tags: list[str] = Field(default_factory=list)


class PostDetailResponse(BaseModel):
    id: int
    title: str
    content: str
    tags: list[TagResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class PostListResponse(BaseModel):
    id: int
    title: str

    model_config = ConfigDict(from_attributes=True)
