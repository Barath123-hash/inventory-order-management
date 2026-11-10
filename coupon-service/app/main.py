import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

app = FastAPI(title="Coupon Service")

security = HTTPBearer()

engine = create_engine(
    "sqlite:///./coupons.db",
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
def create_coupon(
    data: CouponData,
    user_id: int = Depends(verify_token)
):
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
def get_coupon(
    code: str,
    user_id: int = Depends(verify_token)
):
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