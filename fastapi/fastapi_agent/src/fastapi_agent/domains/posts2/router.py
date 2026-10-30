from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_agent.core.database import get_db
from fastapi_agent.core.responses import SuccessResponse, error_responses
from fastapi_agent.domains.posts2.schemas import (
    Post2PageResponse,
    Post2Query,
    Post2SetupResponse,
)
from fastapi_agent.domains.posts2.service import post2_service

router = APIRouter(prefix="/posts2", tags=["posts2"], responses=error_responses(422))


@router.post(
    "/setup",
    response_model=SuccessResponse[Post2SetupResponse],
    summary="posts2 실습 데이터 초기화",
    description="posts2 테이블의 데이터를 삭제한 뒤 지정한 개수만큼 생성합니다.",
)
async def setup(
    db: Annotated[AsyncSession, Depends(get_db)],
    count: Annotated[int, Query(ge=1, le=100)] = 40,
):
    result = await post2_service.setup(db, count)
    return SuccessResponse[Post2SetupResponse](data=result)


@router.get("", response_model=SuccessResponse[Post2PageResponse])
async def get_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[Post2Query, Query()],
):
    result = await post2_service.get_posts(db, params)
    return SuccessResponse[Post2PageResponse](data=result)
