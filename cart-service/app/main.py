
import os
from dotenv import load_dotenv
from jose import jwt, JWTError

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

bearer_scheme = HTTPBearer()

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
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


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
    return {"message": "Cart Service is running"}


@app.post("/cart")
def add_to_cart(
    data: CartData,
    token_data: dict = Depends(verify_token)
):
    user_id = int(token_data["sub"])

    db = SessionLocal()
    try:
        item = db.query(CartItem).filter(
            CartItem.user_id == user_id,
            CartItem.product_id == data.product_id
        ).first()

        if item:
            item.quantity += data.quantity
        else:
            item = CartItem(
                user_id=user_id,
                product_id=data.product_id,
                quantity=data.quantity
            )
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


@app.get("/cart")
def view_cart(
    token_data: dict = Depends(verify_token)
):
    user_id = int(token_data["sub"])

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
def remove_from_cart(
    cart_id: int,
    token_data: dict = Depends(verify_token)
):
    user_id = int(token_data["sub"])

    db = SessionLocal()
    try:
        item = db.query(CartItem).filter(
            CartItem.id == cart_id,
            CartItem.user_id == user_id
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
