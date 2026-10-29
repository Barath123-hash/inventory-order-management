
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

app = FastAPI(title="Product Catalog Service")

engine = create_engine(
    "sqlite:///./products.db",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, default="")
    category = Column(String, nullable=False)
    price = Column(Float, nullable=False)


Base.metadata.create_all(bind=engine)


class ProductData(BaseModel):
    name: str
    description: str = ""
    category: str
    price: float = Field(gt=0)


@app.get("/")
def home():
    return {"message": "Product Service is running"}


@app.post("/products")
def create_product(data: ProductData):
    db = SessionLocal()
    try:
        product = Product(**data.model_dump())
        db.add(product)
        db.commit()
        db.refresh(product)

        return {
            "message": "Product created",
            "id": product.id,
            "name": product.name,
            "price": product.price
        }
    finally:
        db.close()


@app.get("/products")
def get_products():
    db = SessionLocal()
    try:
        products = db.query(Product).all()
        return [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "price": p.price
            }
            for p in products
        ]
    finally:
        db.close()


@app.get("/products/{product_id}")
def get_product(product_id: int):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found")

        return {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "category": product.category,
            "price": product.price
        }
    finally:
        db.close()
