from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from mysite_many_to_many.models.post_mn import PostMN
from mysite_many_to_many.models.tag_mn import TagMN
from mysite_many_to_many.repositories.post_repository import post_repository
from mysite_many_to_many.repositories.post_tag_repository import post_tag_repository
from mysite_many_to_many.repositories.tag_repository import tag_repository
from mysite_many_to_many.schemas.post import PostCreate, PostCreateWithTags
from mysite_many_to_many.schemas.tag import TagCreate


class PostService:
    def create_post(self, db: Session, data: PostCreate):
        with db.begin():
            new_post = PostMN(title=data.title, content=data.content)
            post_repository.save(db, new_post)

        return new_post

    def get_posts(self, db: Session):
        return post_repository.find_all(db)

    def get_post(self, db: Session, post_id: int):
        post = post_repository.find_by_id(db, post_id)
        if post is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="게시글을 찾을 수 없습니다.",
            )
        return post

    def update_post(self, db: Session, post_id: int, data: PostCreate):
        with db.begin():
            post = self.get_post(db, post_id)
            updated_post = post_repository.update(db, post, data)

        return updated_post

    def delete_post(self, db: Session, post_id: int):
        with db.begin():
            post = self.get_post(db, post_id)
            post_repository.delete(db, post)

    def add_tag_to_post(self, db: Session, post_id: int, data: TagCreate):
        with db.begin():
            post = self.get_post(db, post_id)
            tag = tag_repository.find_by_name(db, data.name)
            if tag is None:
                tag = TagMN(name=data.name)
            elif post_tag_repository.exists(db, post.id, tag.id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 이 게시글에 등록된 태그입니다.",
                )

            post.tags.append(tag)

        return post

    def create_post_with_tags(self, db: Session, data: PostCreateWithTags):
        with db.begin():
            names = list(dict.fromkeys(data.tags))
            tags_by_name = {
                tag.name: tag for tag in tag_repository.find_by_names(db, names)
            }
            new_post = PostMN(title=data.title, content=data.content)

            for name in names:
                tag = tags_by_name.get(name)
                if tag is None:
                    tag = TagMN(name=name)
                new_post.tags.append(tag)

            post_repository.save(db, new_post)

        return new_post

    def remove_tag_from_post(self, db: Session, post_id: int, tag_id: int):
        with db.begin():
            post = self.get_post(db, post_id)
            tag = next((tag for tag in post.tags if tag.id == tag_id), None)
            if tag is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="해당 게시글에 연결된 태그를 찾을 수 없습니다.",
                )
            post.tags.remove(tag)


post_service = PostService()
