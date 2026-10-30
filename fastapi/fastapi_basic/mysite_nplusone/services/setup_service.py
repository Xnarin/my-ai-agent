from sqlalchemy.orm import Session

from mysite_nplusone.models import CommentNPlusOne, PostNPlusOne, UserNPlusOne
from mysite_nplusone.repositories.setup_repository import setup_repository
from mysite_nplusone.schemas.setup import SetupResponse


class SetupService:
    def setup(self, db: Session):
        with db.begin():
            setup_repository.clear(db)
            users = [
                UserNPlusOne(name=name)
                for name in ("Alice", "Bob", "Charlie", "David", "Eve")
            ]

            for user in users:
                for post_number in range(1, 6):
                    post = PostNPlusOne(title=f"{user.name}의 게시글 {post_number}")
                    post.comments = [
                        CommentNPlusOne(
                            content=f"{post.title}의 댓글 {number}", user=comment_user
                        )
                        for number, comment_user in enumerate(users, start=1)
                    ]
                    user.posts.append(post)

            setup_repository.save_users(db, users)
            result = SetupResponse(
                users=len(users),
                posts=sum(len(user.posts) for user in users),
                comments=sum(
                    len(post.comments) for user in users for post in user.posts
                ),
            )

        return result


setup_service = SetupService()
