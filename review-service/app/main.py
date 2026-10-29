from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

app = FastAPI(title="Review Service")

engine = create_engine(
    "sqlite:///./reviews.db",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, default="")


Base.metadata.create_all(bind=engine)


class ReviewData(BaseModel):
    user_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)
    comment: str = ""


@app.get("/")
def home():
    return {"message": "Review Service is running"}


@app.post("/reviews")
def create_review(data: ReviewData):
    db = SessionLocal()
    try:
        review = Review(**data.model_dump())
        db.add(review)
        db.commit()
        db.refresh(review)

        return {
            "message": "Review added successfully",
            "review_id": review.id,
            "product_id": review.product_id,
            "rating": review.rating,
            "comment": review.comment
        }
    finally:
        db.close()


@app.get("/reviews/{product_id}")
def get_reviews(product_id: int):
    db = SessionLocal()
    try:
        reviews = db.query(Review).filter(
            Review.product_id == product_id
        ).all()

        return [
            {
                "review_id": r.id,
                "user_id": r.user_id,
                "rating": r.rating,
                "comment": r.comment
            }
            for r in reviews
        ]
    finally:
        db.close()