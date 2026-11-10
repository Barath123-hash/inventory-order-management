import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

app = FastAPI(title="Review Service")

security = HTTPBearer()

engine = create_engine(
    "sqlite:///./reviews.db",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return int(user_id)

    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text, default="")


Base.metadata.create_all(bind=engine)


class ReviewData(BaseModel):
    product_id: int = Field(gt=0)
    rating: int = Field(ge=1, le=5)
    comment: str = ""


@app.get("/")
def home():
    return {"message": "Review Service is running"}


@app.post("/reviews")
def create_review(
    data: ReviewData,
    user_id: int = Depends(verify_token)
):
    db = SessionLocal()

    try:
        review = Review(
            user_id=user_id,
            product_id=data.product_id,
            rating=data.rating,
            comment=data.comment
        )

        db.add(review)
        db.commit()
        db.refresh(review)

        return {
            "message": "Review added successfully",
            "review_id": review.id,
            "user_id": review.user_id,
            "product_id": review.product_id,
            "rating": review.rating,
            "comment": review.comment
        }

    finally:
        db.close()


@app.get("/reviews/{product_id}")
def get_reviews(
    product_id: int,
    user_id: int = Depends(verify_token)
):
    db = SessionLocal()

    try:
        reviews = db.query(Review).filter(
            Review.product_id == product_id,
            Review.user_id == user_id
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