from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from .post_1n import Post1N


class Comment1N(Base):
    __tablename__ = "comment_1n"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(String(200), nullable=False)
    post_id: Mapped[int] = mapped_column(ForeignKey("post_1n.id"), nullable=False)

    post: Mapped["Post1N"] = relationship("Post1N", back_populates="comments")
