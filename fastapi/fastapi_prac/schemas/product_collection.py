from pydantic import BaseModel, ConfigDict


class ProductCollectionCreate(BaseModel):
    product_id: int


class ProductCollectionResponse(BaseModel):
    id: int
    product_id: int
    collection_id: int

    model_config = ConfigDict(from_attributes=True)
