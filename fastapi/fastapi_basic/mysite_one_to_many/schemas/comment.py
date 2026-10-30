from pydantic import BaseModel, ConfigDict, Field


class CommentCreate(BaseModel):
    content: str = Field(min_length=1, max_length=200)


class CommentResponse(BaseModel):
    id: int
    content: str

    model_config = ConfigDict(from_attributes=True)
