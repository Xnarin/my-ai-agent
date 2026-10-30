from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from schemas.collection import (
    CollectionCreate,
    CollectionDetailResponse,
    CollectionResponse,
)
from schemas.product_collection import (
    ProductCollectionCreate,
    ProductCollectionResponse,
)
from services.collection_service import collection_service

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(data: CollectionCreate, db: Annotated[Session, Depends(get_db)]):
    return collection_service.create_collection(db, data)


@router.get("", response_model=list[CollectionResponse])
def get_collections(db: Annotated[Session, Depends(get_db)]):
    return collection_service.get_collections(db)


@router.get("/{collection_id}", response_model=CollectionDetailResponse)
def get_collection(collection_id: int, db: Annotated[Session, Depends(get_db)]):
    return collection_service.get_collection(db, collection_id)


@router.post(
    "/{collection_id}/products",
    response_model=ProductCollectionResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_product_to_collection(
    collection_id: int,
    data: ProductCollectionCreate,
    db: Annotated[Session, Depends(get_db)],
):
    return collection_service.add_product_to_collection(db, collection_id, data)


@router.delete(
    "/{collection_id}/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT
)
def remove_product_from_collection(
    collection_id: int, product_id: int, db: Annotated[Session, Depends(get_db)]
):
    collection_service.remove_product_from_collection(db, collection_id, product_id)
