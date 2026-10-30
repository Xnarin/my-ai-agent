from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import Base, engine
from mysite.post_api import router as post_router
from mysite2.post_api import router as pydantic_router
from mysite3.post_api import router as response_router
from mysite4.routers.post_router import router as layered_router
from mysite_auth import models as auth_models
from mysite_auth.routers.auth_router import router as auth_router
from mysite_auth.routers.post_router import router as auth_post_router
from mysite_auth.routers.user_router import router as user_router
from mysite_db import models
from mysite_db.routers.post_router import router as db_router
from mysite_many_to_many import models as many_to_many_models
from mysite_many_to_many.routers.post_router import router as many_to_many_post_router
from mysite_many_to_many.routers.tag_router import router as many_to_many_tag_router
from mysite_nplusone import models as nplusone_models
from mysite_nplusone.routers.post_router import router as nplusone_router
from mysite_one_to_many import models as one_to_many_models
from mysite_one_to_many.routers.post_router import router as one_to_many_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
        yield
    finally:
        engine.dispose()


app = FastAPI(lifespan=lifespan)
app.include_router(post_router)
app.include_router(pydantic_router)
app.include_router(response_router)
app.include_router(layered_router)
app.include_router(db_router)
app.include_router(one_to_many_router)
app.include_router(many_to_many_post_router)
app.include_router(many_to_many_tag_router)
app.include_router(nplusone_router)
app.include_router(auth_router)
app.include_router(auth_post_router)
app.include_router(user_router)


@app.get("/")
def get_root():
    return {"Hello": "World"}
