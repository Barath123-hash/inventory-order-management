from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

app = FastAPI(title="Coupon Service")

engine = create_engine(
    "sqlite:///./coupons.db",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    discount_percent = Column(Float, nullable=False)


Base.metadata.create_all(bind=engine)


class CouponData(BaseModel):
    code: str
    discount_percent: float = Field(gt=0, le=100)


@app.get("/")
def home():
    return {"message": "Coupon Service is running"}


@app.post("/coupons")
def create_coupon(data: CouponData):
    db = SessionLocal()
    try:
        code = data.code.strip().upper()

        existing = db.query(Coupon).filter(
            Coupon.code == code
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Coupon already exists"
            )

        coupon = Coupon(
            code=code,
            discount_percent=data.discount_percent
        )
        db.add(coupon)
        db.commit()
        db.refresh(coupon)

        return {
            "message": "Coupon created successfully",
            "code": coupon.code,
            "discount_percent": coupon.discount_percent
        }
    finally:
        db.close()


@app.get("/coupons/{code}")
def get_coupon(code: str):
    db = SessionLocal()
    try:
        coupon = db.query(Coupon).filter(
            Coupon.code == code.strip().upper()
        ).first()

        if not coupon:
            raise HTTPException(
                status_code=404,
                detail="Coupon not found"
            )

        return {
            "code": coupon.code,
            "discount_percent": coupon.discount_percent
        }
    finally:
        db.close()