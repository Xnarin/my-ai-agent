from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.collection import Collection
from models.product_collection import ProductCollection
from repositories.collection_repository import collection_repository
from repositories.product_collection_repository import product_collection_repository
from schemas.collection import CollectionCreate
from schemas.product_collection import ProductCollectionCreate
from services.product_service import product_service


class CollectionService:
    def create_collection(self, db: Session, data: CollectionCreate):
        with db.begin():
            new_collection = Collection(name=data.name)
            collection_repository.save(db, new_collection)

        return new_collection

    def get_collections(self, db: Session):
        return collection_repository.find_all(db)

    def get_collection(self, db: Session, collection_id: int):
        collection = collection_repository.find_by_id(db, collection_id)
        if collection is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="기획전을 찾을 수 없습니다.",
            )
        return collection

    def add_product_to_collection(
        self, db: Session, collection_id: int, data: ProductCollectionCreate
    ):
        with db.begin():
            collection = self.get_collection(db, collection_id)
            product = product_service.get_product_or_404(db, data.product_id)
            if product_collection_repository.exists(db, product.id, collection.id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 이 기획전에 연결된 상품입니다.",
                )

            product_collection = ProductCollection(product_id=product.id)
            collection.product_collections.append(product_collection)

        return product_collection

    def remove_product_from_collection(
        self, db: Session, collection_id: int, product_id: int
    ):
        with db.begin():
            collection = self.get_collection(db, collection_id)
            product = next(
                (product for product in collection.products if product.id == product_id),
                None,
            )
            if product is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="해당 기획전에 연결된 상품을 찾을 수 없습니다.",
                )
            collection.products.remove(product)


collection_service = CollectionService()
