from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from .post_nplusone import PostNPlusOne
    from .user_nplusone import UserNPlusOne


class CommentNPlusOne(Base):
    __tablename__ = "comment_nplusone"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(String(200), nullable=False)
    post_id: Mapped[int] = mapped_column(
        ForeignKey("post_nplusone.id"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user_nplusone.id"), nullable=False
    )

    post: Mapped["PostNPlusOne"] = relationship(
        "PostNPlusOne", back_populates="comments"
    )
    user: Mapped["UserNPlusOne"] = relationship(
        "UserNPlusOne", back_populates="comments"
    )
