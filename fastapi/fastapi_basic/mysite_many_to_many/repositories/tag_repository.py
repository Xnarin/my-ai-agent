from sqlalchemy import select
from sqlalchemy.orm import Session

from mysite_many_to_many.models.tag_mn import TagMN


class TagRepository:
    def save(self, db: Session, tag: TagMN):
        db.add(tag)
        return tag

    def find_all(self, db: Session):
        return db.scalars(select(TagMN).order_by(TagMN.id)).all()

    def find_by_name(self, db: Session, name: str):
        return db.scalar(select(TagMN).where(TagMN.name == name))

    def find_by_names(self, db: Session, names: list[str]):
        if not names:
            return []
        return db.scalars(select(TagMN).where(TagMN.name.in_(names))).all()


tag_repository = TagRepository()
