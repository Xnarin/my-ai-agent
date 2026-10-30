from fastapi import APIRouter, status

from schemas.product import (
    ProductDetailResponse,
    ProductListResponse,
    ProductRequest,
)
from services.product_service import product_service

router = APIRouter(prefix="/products", tags=["products"])


@router.post("", response_model=ProductDetailResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductRequest):
    return product_service.create_product(data)


@router.get("", response_model=list[ProductListResponse])
def get_products(keyword: str | None = None):
    return product_service.get_products(keyword)


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product(product_id: int):
    return product_service.get_product(product_id)


@router.put("/{product_id}", response_model=ProductDetailResponse)
def update_product(product_id: int, data: ProductRequest):
    return product_service.update_product(product_id, data)
