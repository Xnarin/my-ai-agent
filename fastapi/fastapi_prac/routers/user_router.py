from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_user
from schemas.user import UserResponse
from schemas.wishlist_item import (
    WishlistItemCreate,
    WishlistItemListResponse,
    WishlistItemResponse,
)
from services.wishlist_service import wishlist_service

router = APIRouter(prefix="/me", tags=["users"])


@router.get("", response_model=UserResponse)
def get_me(current_user: Annotated[UserResponse, Depends(get_current_user)]):
    return current_user


@router.post(
    "/wishlist",
    response_model=WishlistItemResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_product_to_wishlist(
    data: WishlistItemCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    return wishlist_service.add_product(db, data, current_user)


@router.get("/wishlist", response_model=list[WishlistItemListResponse])
def get_wishlist(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    return wishlist_service.get_wishlist(db, current_user.id)


@router.delete("/wishlist/{wishlist_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wishlist_item(
    wishlist_item_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[UserResponse, Depends(get_current_user)],
):
    wishlist_service.delete_item(db, wishlist_item_id, current_user)
