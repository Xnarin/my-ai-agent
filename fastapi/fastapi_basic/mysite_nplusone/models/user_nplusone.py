from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from .comment_nplusone import CommentNPlusOne
    from .post_nplusone import PostNPlusOne


class UserNPlusOne(Base):
    __tablename__ = "user_nplusone"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    posts: Mapped[list["PostNPlusOne"]] = relationship(
        "PostNPlusOne", back_populates="user", order_by="PostNPlusOne.id"
    )
    comments: Mapped[list["CommentNPlusOne"]] = relationship(
        "CommentNPlusOne", back_populates="user", order_by="CommentNPlusOne.id"
    )
