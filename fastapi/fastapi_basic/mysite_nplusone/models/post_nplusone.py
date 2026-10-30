from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from .comment_nplusone import CommentNPlusOne
    from .user_nplusone import UserNPlusOne


class PostNPlusOne(Base):
    __tablename__ = "post_nplusone"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_nplusone.id"), nullable=False
    )

    user: Mapped["UserNPlusOne"] = relationship(
        "UserNPlusOne", back_populates="posts"
    )
    comments: Mapped[list["CommentNPlusOne"]] = relationship(
        "CommentNPlusOne",
        back_populates="post",
        order_by="CommentNPlusOne.id",
    )
