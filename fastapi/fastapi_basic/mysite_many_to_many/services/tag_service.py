from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from mysite_many_to_many.models.tag_mn import TagMN
from mysite_many_to_many.repositories.tag_repository import tag_repository
from mysite_many_to_many.schemas.tag import TagCreate


class TagService:
    def create_tag(self, db: Session, data: TagCreate):
        with db.begin():
            if tag_repository.find_by_name(db, data.name) is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 존재하는 태그 이름입니다.",
                )
            new_tag = TagMN(name=data.name)
            tag_repository.save(db, new_tag)

        return new_tag

    def get_tags(self, db: Session):
        return tag_repository.find_all(db)


tag_service = TagService()
