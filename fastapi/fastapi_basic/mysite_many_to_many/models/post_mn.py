from typing import TYPE_CHECKING

from sqlalchemy import String, Text
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from .post_tag_mn import PostTagMN

if TYPE_CHECKING:
    from .tag_mn import TagMN


class PostMN(Base):
    __tablename__ = "post_mn"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    post_tags: Mapped[list["PostTagMN"]] = relationship(
        "PostTagMN",
        back_populates="post",
        cascade="all, delete-orphan",
        order_by="PostTagMN.id",
    )
    tags: AssociationProxy[list["TagMN"]] = association_proxy(
        "post_tags", "tag", creator=lambda tag: PostTagMN(tag=tag)
    )
