from sqlalchemy import select
from sqlalchemy.orm import Session

from mysite_many_to_many.models.post_tag_mn import PostTagMN


class PostTagRepository:
    def exists(self, db: Session, post_id: int, tag_id: int):
        stmt = (
            select(PostTagMN.id)
            .where(PostTagMN.post_id == post_id, PostTagMN.tag_id == tag_id)
            .exists()
        )
        return db.scalar(select(stmt))


post_tag_repository = PostTagRepository()
