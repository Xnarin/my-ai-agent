from pydantic import BaseModel, ConfigDict, Field

from schemas.product import ProductListResponse


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)


class CollectionResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class CollectionDetailResponse(BaseModel):
    id: int
    name: str
    products: list[ProductListResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
