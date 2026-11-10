
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

app = FastAPI(title="Inventory Service")

engine = create_engine(
    "sqlite:///./inventory.db",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, unique=True, nullable=False)
    quantity = Column(Integer, default=0, nullable=False)


Base.metadata.create_all(bind=engine)


class StockData(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=0)


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
    return {"message": "Inventory Service is running"}


@app.post("/inventory")
def add_stock(
    data: StockData,
    token_data: dict = Depends(verify_token)
):
    db = SessionLocal()
    try:
        stock = db.query(Inventory).filter(
            Inventory.product_id == data.product_id
        ).first()

        if stock:
            stock.quantity = data.quantity
        else:
            stock = Inventory(
                product_id=data.product_id,
                quantity=data.quantity
            )
            db.add(stock)

        db.commit()
        db.refresh(stock)

        return {
            "message": "Stock saved successfully",
            "product_id": stock.product_id,
            "quantity": stock.quantity
        }
    finally:
        db.close()


@app.get("/inventory/{product_id}")
def get_stock(product_id: int):
    db = SessionLocal()
    try:
        stock = db.query(Inventory).filter(
            Inventory.product_id == product_id
        ).first()

        if not stock:
            raise HTTPException(
                status_code=404,
                detail="Stock not found"
            )

        return {
            "product_id": stock.product_id,
            "quantity": stock.quantity
        }
    finally:
        db.close()
