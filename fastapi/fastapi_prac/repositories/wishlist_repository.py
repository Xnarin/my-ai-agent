from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from models.wishlist_item import WishlistItem


class WishlistRepository:
    def save(self, db: Session, item: WishlistItem):
        db.add(item)
        return item

    def find_by_id(self, db: Session, wishlist_item_id: int):
        return db.get(WishlistItem, wishlist_item_id)

    def find_by_user_id(self, db: Session, user_id: int):
        stmt = (
            select(WishlistItem)
            .options(selectinload(WishlistItem.product))
            .where(WishlistItem.user_id == user_id)
            .order_by(WishlistItem.id)
        )
        return db.scalars(stmt).all()

    def exists(self, db: Session, user_id: int, product_id: int):
        stmt = (
            select(WishlistItem.id)
            .where(
                WishlistItem.user_id == user_id,
                WishlistItem.product_id == product_id,
            )
            .exists()
        )
        return db.scalar(select(stmt))

    def delete(self, db: Session, item: WishlistItem):
        db.delete(item)


wishlist_repository = WishlistRepository()
