from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from models.review import Review
from repositories.review_repository import review_repository
from schemas.review import ReviewCreate
from services.product_service import product_service


class ReviewService:
    def create_review(self, db: Session, product_id: int, data: ReviewCreate):
        with db.begin():
            product = product_service.get_product_or_404(db, product_id)
            new_review = Review(
                content=data.content,
                rating=data.rating,
                product=product,
            )
            review_repository.save(db, new_review)

        return new_review

    def update_review(
        self, db: Session, product_id: int, review_id: int, data: ReviewCreate
    ):
        with db.begin():
            review = self._get_verified_review(db, product_id, review_id)
            updated_review = review_repository.update(db, review, data)

        return updated_review

    def delete_review(self, db: Session, product_id: int, review_id: int):
        with db.begin():
            review = self._get_verified_review(db, product_id, review_id)
            review_repository.delete(db, review)

    def _get_verified_review(self, db: Session, product_id: int, review_id: int):
        review = review_repository.find_by_id(db, review_id)
        if review is None or review.product_id != product_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 상품의 리뷰를 찾을 수 없습니다.",
            )
        return review


review_service = ReviewService()
