from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from sqlalchemy.engine import make_url

from agents import create_chat_agent, create_rag_agent
from fastapi_agent.core.config import get_settings
from fastapi_agent.core.database import engine
from fastapi_agent.core.exception_handlers import register_exception_handlers
from fastapi_agent.core.responses import SuccessResponse, error_responses
from fastapi_agent.domains.chat.router import router as chat_router
from fastapi_agent.domains.comments.router import router as comment_router
from fastapi_agent.domains.posts.router import router as post_router
from fastapi_agent.domains.posts2.router import router as post2_router
from fastapi_agent.domains.users.router import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        app.state.rag_agent = create_rag_agent()
        checkpoint_url = make_url(get_settings().database_url).set(drivername="postgresql")
        async with AsyncPostgresSaver.from_conn_string(
            checkpoint_url.render_as_string(hide_password=False)
        ) as checkpointer:
            await checkpointer.setup()
            app.state.chat_agent = create_chat_agent(checkpointer)
            yield
    finally:
        await engine.dispose()


app = FastAPI(title="FastAPI Agent", lifespan=lifespan, responses=error_responses(500))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
register_exception_handlers(app)
app.include_router(user_router)
app.include_router(post_router)
app.include_router(post2_router)
app.include_router(comment_router)
app.include_router(chat_router)


@app.get("/", response_model=SuccessResponse[dict[str, str]])
async def get_root():
    return SuccessResponse[dict[str, str]](data={"Hello": "World"})
