from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base
from .product_collection import ProductCollection

if TYPE_CHECKING:
    from .product import Product


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    product_collections: Mapped[list["ProductCollection"]] = relationship(
        "ProductCollection",
        back_populates="collection",
        cascade="all, delete-orphan",
        order_by="ProductCollection.id",
    )
    products: AssociationProxy[list["Product"]] = association_proxy(
        "product_collections",
        "product",
        creator=lambda product: ProductCollection(product=product),
    )
