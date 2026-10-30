from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from mysite_many_to_many.schemas.tag import TagCreate, TagResponse
from mysite_many_to_many.services.tag_service import tag_service

router = APIRouter(prefix="/tags-mn", tags=["mysite_many_to_many"])


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
def create_tag(data: TagCreate, db: Annotated[Session, Depends(get_db)]):
    return tag_service.create_tag(db, data)


@router.get("", response_model=list[TagResponse])
def get_tags(db: Annotated[Session, Depends(get_db)]):
    return tag_service.get_tags(db)
