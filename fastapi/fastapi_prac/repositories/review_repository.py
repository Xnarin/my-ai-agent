from sqlalchemy.orm import Session

from models.review import Review
from schemas.review import ReviewCreate


class ReviewRepository:
    def save(self, db: Session, new_review: Review):
        db.add(new_review)
        return new_review

    def find_by_id(self, db: Session, review_id: int):
        return db.get(Review, review_id)

    def update(self, db: Session, review: Review, data: ReviewCreate):
        review.content = data.content
        review.rating = data.rating
        return review

    def delete(self, db: Session, review: Review):
        db.delete(review)


review_repository = ReviewRepository()
