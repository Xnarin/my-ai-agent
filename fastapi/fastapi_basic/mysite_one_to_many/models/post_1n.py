from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from .comment_1n import Comment1N


class Post1N(Base):
    __tablename__ = "post_1n"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    comments: Mapped[list["Comment1N"]] = relationship(
        "Comment1N",
        back_populates="post",
        cascade="all",
        order_by="Comment1N.id",
    )
