from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import declarative_base, sessionmaker
import uuid

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
    order_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="SUCCESS")
    transaction_id = Column(String, unique=True, nullable=False)


Base.metadata.create_all(bind=engine)


class PaymentData(BaseModel):
    order_id: int = Field(gt=0)
    amount: float = Field(gt=0)


@app.get("/")
def home():
    return {"message": "Payment Service is running"}


@app.post("/payments")
def make_payment(data: PaymentData):
    db = SessionLocal()
    try:
        transaction_id = "TEST-" + uuid.uuid4().hex[:10].upper()

        payment = Payment(
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
            "order_id": payment.order_id,
            "amount": payment.amount,
            "status": payment.status,
            "transaction_id": payment.transaction_id
        }
    finally:
        db.close()


@app.get("/payments/{order_id}")
def get_payment(order_id: int):
    db = SessionLocal()
    try:
        payments = db.query(Payment).filter(
            Payment.order_id == order_id
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