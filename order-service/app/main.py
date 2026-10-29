from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import declarative_base, sessionmaker

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
    user_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    unit_price: float = Field(gt=0)


@app.get("/")
def home():
    return {"message": "Order Service is running"}


@app.post("/orders")
def create_order(data: OrderData):
    db = SessionLocal()
    try:
        total = data.quantity * data.unit_price

        order = Order(
            user_id=data.user_id,
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


@app.get("/orders/{user_id}")
def get_orders(user_id: int):
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
def update_order_status(order_id: int, status: str):
    allowed_statuses = ["PLACED", "CONFIRMED", "SHIPPED", "DELIVERED", "CANCELLED"]

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid order status"
        )

    db = SessionLocal()
    try:
        order = db.query(Order).filter(
            Order.id == order_id
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