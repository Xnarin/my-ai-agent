from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

if TYPE_CHECKING:
    from .collection import Collection
    from .product import Product


class ProductCollection(Base):
    __tablename__ = "product_collections"
    __table_args__ = (
        UniqueConstraint(
            "product_id", "collection_id", name="uq_product_collections_product_collection"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    collection_id: Mapped[int] = mapped_column(ForeignKey("collections.id"), nullable=False)

    product: Mapped["Product"] = relationship(
        "Product", back_populates="product_collections"
    )
    collection: Mapped["Collection"] = relationship(
        "Collection", back_populates="product_collections"
    )
