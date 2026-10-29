from fastapi import FastAPI
from sqlalchemy import create_engine, text

app = FastAPI(title="Analytics Service")

engine = create_engine(
    "sqlite:///./orders.db",
    connect_args={"check_same_thread": False}
)


@app.get("/")
def home():
    return {"message": "Analytics Service is running"}


@app.get("/analytics/orders")
def order_analytics():
    with engine.connect() as connection:
        try:
            result = connection.execute(
                text("""
                    SELECT
                        COUNT(*) AS total_orders,
                        COALESCE(SUM(total_amount), 0) AS total_sales
                    FROM orders
                """)
            )
            row = result.fetchone()

            return {
                "total_orders": row[0],
                "total_sales": row[1]
            }
        except Exception:
            return {
                "total_orders": 0,
                "total_sales": 0,
                "note": "Order database not available yet"
            }