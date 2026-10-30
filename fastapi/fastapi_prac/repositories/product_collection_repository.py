from sqlalchemy import select
from sqlalchemy.orm import Session

from models.product_collection import ProductCollection


class ProductCollectionRepository:
    def exists(self, db: Session, product_id: int, collection_id: int):
        stmt = (
            select(ProductCollection.id)
            .where(
                ProductCollection.product_id == product_id,
                ProductCollection.collection_id == collection_id,
            )
            .exists()
        )
        return db.scalar(select(stmt))


product_collection_repository = ProductCollectionRepository()
