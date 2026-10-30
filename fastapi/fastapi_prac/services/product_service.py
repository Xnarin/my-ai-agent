from fastapi import HTTPException, status

from repositories.product_repository import product_repository
from schemas.product import (
    Product,
    ProductDetailResponse,
    ProductListResponse,
    ProductRequest,
)


class ProductService:
    def create_product(self, data: ProductRequest):
        if data.discount_price >= data.price:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="할인 금액은 가격보다 작아야 합니다.",
            )

        new_product = Product(
            name=data.name,
            price=data.price,
            discount_price=data.discount_price,
            stock=data.stock,
            category=data.category,
        )
        product = product_repository.save(new_product)
        return self.to_detail_response(product)

    def get_products(self, keyword: str | None = None):
        products = product_repository.find_all(keyword)
        return [
            ProductListResponse(
                id=product.id,
                name=product.name,
                final_price=product.price - product.discount_price,
                category=product.category,
            )
            for product in products
        ]

    def get_product(self, product_id: int):
        product = product_repository.find_by_id(product_id)
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="상품을 찾을 수 없습니다.",
            )
        return self.to_detail_response(product)

    def update_product(self, product_id: int, data: ProductRequest):
        if data.discount_price >= data.price:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="할인 금액은 가격보다 작아야 합니다.",
            )

        self.get_product(product_id)
        product = product_repository.update(product_id, data)
        return self.to_detail_response(product)

    def to_detail_response(self, product: Product):
        return ProductDetailResponse(
            id=product.id,
            name=product.name,
            final_price=product.price - product.discount_price,
            category=product.category,
            stock=product.stock,
            is_sold_out=product.stock == 0,
        )


product_service = ProductService()
