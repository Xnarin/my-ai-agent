from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.wishlist_item import WishlistItem
from repositories.wishlist_repository import wishlist_repository
from schemas.user import UserResponse
from schemas.wishlist_item import WishlistItemCreate
from services.product_service import product_service


class WishlistService:
    def add_product(
        self, db: Session, data: WishlistItemCreate, current_user: UserResponse
    ):
        with db.begin():
            product = product_service.get_product_or_404(db, data.product_id)
            if wishlist_repository.exists(db, current_user.id, product.id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 위시리스트에 담은 상품입니다.",
                )

            item = WishlistItem(user_id=current_user.id, product_id=product.id)
            wishlist_repository.save(db, item)

        return item

    def get_wishlist(self, db: Session, user_id: int):
        return wishlist_repository.find_by_user_id(db, user_id)

    def delete_item(
        self, db: Session, wishlist_item_id: int, current_user: UserResponse
    ):
        with db.begin():
            item = wishlist_repository.find_by_id(db, wishlist_item_id)
            if item is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="위시리스트 항목을 찾을 수 없습니다.",
                )
            if item.user_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="본인의 위시리스트 항목만 삭제할 수 있습니다.",
                )
            wishlist_repository.delete(db, item)


wishlist_service = WishlistService()
