from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Product(Base):
    __tablename__ = "products"

    # id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    # title: Mapped[str] = mapped_column(String(50), nullable=False)
    # content: Mapped[str] = mapped_column(Text, nullable=False)

    id : Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name : Mapped[str] = mapped_column(Text, nullable=False)
    price : Mapped[int] = mapped_column()
    discount_price : Mapped[int] = mapped_column()
    stock : Mapped[int] = mapped_column()
    category : Mapped[str] = mapped_column(Text, nullable=False)