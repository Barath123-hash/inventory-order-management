
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer
from sqlalchemy.orm import declarative_base, sessionmaker

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


@app.get("/")
def home():
    return {"message": "Inventory Service is running"}


@app.post("/inventory")
def add_stock(data: StockData):
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
