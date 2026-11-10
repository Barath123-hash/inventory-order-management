
import os
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

app = FastAPI(title="Order Service")

engine = create_engine(
    "sqlite:///./orders.db",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String, default="PLACED")


Base.metadata.create_all(bind=engine)


class OrderData(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
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
    return {"message": "Order Service is running"}


@app.post("/orders")
def create_order(
    data: OrderData,
    token_data: dict = Depends(verify_token)
):
    user_id = int(token_data["sub"])

    db = SessionLocal()
    try:
        total = data.quantity * data.unit_price

        order = Order(
            user_id=user_id,
            product_id=data.product_id,
            quantity=data.quantity,
            total_amount=total,
            status="PLACED"
        )

        db.add(order)
        db.commit()
        db.refresh(order)

        return {
            "message": "Order placed successfully",
            "order_id": order.id,
            "user_id": order.user_id,
            "product_id": order.product_id,
            "quantity": order.quantity,
            "total_amount": order.total_amount,
            "status": order.status
        }
    finally:
        db.close()


@app.get("/orders")
def get_orders(
    token_data: dict = Depends(verify_token)
):
    user_id = int(token_data["sub"])

    db = SessionLocal()
    try:
        orders = db.query(Order).filter(
            Order.user_id == user_id
        ).all()

        return [
            {
                "order_id": order.id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "total_amount": order.total_amount,
                "status": order.status
            }
            for order in orders
        ]
    finally:
        db.close()


@app.patch("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    status: str,
    token_data: dict = Depends(verify_token)
):
    allowed_statuses = [
        "PLACED", "CONFIRMED", "SHIPPED",
        "DELIVERED", "CANCELLED"
    ]

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid order status"
        )

    db = SessionLocal()
    try:
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == int(token_data["sub"])
        ).first()

        if not order:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        order.status = status
        db.commit()

        return {
            "message": "Order status updated",
            "order_id": order.id,
            "status": order.status
        }
    finally:
        db.close()
