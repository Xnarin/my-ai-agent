from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fastapi_agent.core.database import Base

if TYPE_CHECKING:
    from fastapi_agent.domains.comments.models import Comment
    from fastapi_agent.domains.users.models import User


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    user: Mapped["User"] = relationship(back_populates="posts", lazy="raise")
    comments: Mapped[list["Comment"]] = relationship(
        back_populates="post",
        cascade="save-update, merge, delete, delete-orphan",
        passive_deletes=True,
        order_by="Comment.id",
        lazy="raise",
    )
