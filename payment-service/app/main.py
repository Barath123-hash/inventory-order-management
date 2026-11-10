import os
import uuid

from dotenv import load_dotenv
from jose import jwt, JWTError

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()

app = FastAPI(title="Payment Service")

engine = create_engine(
    "sqlite:///./payments.db",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, default=1)
    order_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="SUCCESS")
    transaction_id = Column(String, unique=True, nullable=False)


Base.metadata.create_all(bind=engine)


class PaymentData(BaseModel):
    order_id: int = Field(gt=0)
    amount: float = Field(gt=0)


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


@app.get("/")
def home():
    return {"message": "Payment Service is running"}


@app.post("/payments")
def make_payment(
    data: PaymentData,
    token_data: dict = Depends(verify_token)
):
    user_id = int(token_data["sub"])

    db = SessionLocal()
    try:
        transaction_id = "TEST-" + uuid.uuid4().hex[:10].upper()

        payment = Payment(
            user_id=user_id,
            order_id=data.order_id,
            amount=data.amount,
            status="SUCCESS",
            transaction_id=transaction_id
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return {
            "message": "Mock payment successful",
            "payment_id": payment.id,
            "user_id": payment.user_id,
            "order_id": payment.order_id,
            "amount": payment.amount,
            "status": payment.status,
            "transaction_id": payment.transaction_id
        }
    finally:
        db.close()


@app.get("/payments/{order_id}")
def get_payment(
    order_id: int,
    token_data: dict = Depends(verify_token)
):
    user_id = int(token_data["sub"])

    db = SessionLocal()
    try:
        payments = db.query(Payment).filter(
            Payment.order_id == order_id,
            Payment.user_id == user_id
        ).all()

        return [
            {
                "payment_id": p.id,
                "order_id": p.order_id,
                "amount": p.amount,
                "status": p.status,
                "transaction_id": p.transaction_id
            }
            for p in payments
        ]
    finally:
        db.close()