from pydantic import BaseModel, ConfigDict, Field

from schemas.product import ProductListResponse


class WishlistItemCreate(BaseModel):
    product_id: int = Field(gt=0)


class WishlistItemResponse(BaseModel):
    id: int
    user_id: int
    product_id: int

    model_config = ConfigDict(from_attributes=True)


class WishlistItemListResponse(BaseModel):
    id: int
    product: ProductListResponse

    model_config = ConfigDict(from_attributes=True)
