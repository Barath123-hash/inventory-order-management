from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

app = FastAPI(title="Cart Service")

engine = create_engine(
    "sqlite:///./cart.db",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    product_id = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)


Base.metadata.create_all(bind=engine)


class CartData(BaseModel):
    user_id: int = Field(gt=0)
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


@app.get("/")
def home():
    return {"message": "Cart Service is running"}


@app.post("/cart")
def add_to_cart(data: CartData):
    db = SessionLocal()
    try:
        item = db.query(CartItem).filter(
            CartItem.user_id == data.user_id,
            CartItem.product_id == data.product_id
        ).first()

        if item:
            item.quantity += data.quantity
        else:
            item = CartItem(**data.model_dump())
            db.add(item)

        db.commit()
        db.refresh(item)

        return {
            "message": "Item added to cart",
            "cart_id": item.id,
            "user_id": item.user_id,
            "product_id": item.product_id,
            "quantity": item.quantity
        }
    finally:
        db.close()


@app.get("/cart/{user_id}")
def view_cart(user_id: int):
    db = SessionLocal()
    try:
        items = db.query(CartItem).filter(
            CartItem.user_id == user_id
        ).all()

        return [
            {
                "cart_id": item.id,
                "user_id": item.user_id,
                "product_id": item.product_id,
                "quantity": item.quantity
            }
            for item in items
        ]
    finally:
        db.close()


@app.delete("/cart/{cart_id}")
def remove_from_cart(cart_id: int):
    db = SessionLocal()
    try:
        item = db.query(CartItem).filter(
            CartItem.id == cart_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=404,
                detail="Cart item not found"
            )

        db.delete(item)
        db.commit()

        return {"message": "Item removed from cart"}
    finally:
        db.close()