from pydantic import BaseModel, ConfigDict, Field


class ReviewCreate(BaseModel):
    content: str = Field(min_length=1)
    rating: int = Field(ge=1, le=5)


class ReviewResponse(BaseModel):
    id: int
    content: str
    rating: int

    model_config = ConfigDict(from_attributes=True)
