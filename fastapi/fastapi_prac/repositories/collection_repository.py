from sqlalchemy import select
from sqlalchemy.orm import Session

from models.collection import Collection


class CollectionRepository:
    def save(self, db: Session, new_collection: Collection):
        db.add(new_collection)
        return new_collection

    def find_all(self, db: Session):
        return db.scalars(select(Collection).order_by(Collection.id)).all()

    def find_by_id(self, db: Session, collection_id: int):
        return db.get(Collection, collection_id)


collection_repository = CollectionRepository()
