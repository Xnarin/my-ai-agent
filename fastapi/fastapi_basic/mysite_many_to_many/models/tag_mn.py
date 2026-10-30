from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from .post_tag_mn import PostTagMN


class TagMN(Base):
    __tablename__ = "tag_mn"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    post_tags: Mapped[list["PostTagMN"]] = relationship(
        "PostTagMN",
        back_populates="tag",
        cascade="all, delete-orphan",
        order_by="PostTagMN.id",
    )
