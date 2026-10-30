from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from .post_mn import PostMN
    from .tag_mn import TagMN


class PostTagMN(Base):
    __tablename__ = "post_tag_mn"
    __table_args__ = (
        UniqueConstraint("post_id", "tag_id", name="uq_post_tag_mn_post_tag"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("post_mn.id"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tag_mn.id"), nullable=False)

    post: Mapped["PostMN"] = relationship("PostMN", back_populates="post_tags")
    tag: Mapped["TagMN"] = relationship("TagMN", back_populates="post_tags")
