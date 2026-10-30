from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from database import get_db
from mysite_auth.schemas.user import TokenResponse, UserCreate, UserLogin, UserResponse
from mysite_auth.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["mysite_auth"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(data: UserCreate, db: Annotated[Session, Depends(get_db)]):
    return auth_service.signup(db, data)


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Annotated[Session, Depends(get_db)], response: Response):
    access_token = auth_service.login(db, data)
    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return TokenResponse(access_token=access_token)
