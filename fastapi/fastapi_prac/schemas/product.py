from pydantic import BaseModel, Field


class Product:
    def __init__(self, name, price, discount_price, stock, category):
        self.id = None
        self.name = name
        self.price = price
        self.discount_price = discount_price
        self.stock = stock
        self.category = category


class ProductRequest(BaseModel):
    name: str = Field(min_length=2, max_length=50)
    price: int = Field(ge=100)
    discount_price: int = Field(default=0, ge=0)
    stock: int = Field(default=10, ge=0)
    category: str = Field(min_length=2)


class ProductListResponse(BaseModel):
    id: int
    name: str
    final_price: int
    category: str


class ProductDetailResponse(BaseModel):
    id: int
    name: str
    final_price: int
    category: str
    stock: int
    is_sold_out: bool
