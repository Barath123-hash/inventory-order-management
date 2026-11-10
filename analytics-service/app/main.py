import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy import create_engine, text

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

app = FastAPI(title="Analytics Service")

security = HTTPBearer()

engine = create_engine(
    "sqlite:///./orders.db",
    connect_args={"check_same_thread": False}
)


def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return int(user_id)

    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")


@app.get("/")
def home():
    return {"message": "Analytics Service is running"}


@app.get("/analytics/orders")
def order_analytics(user_id: int = Depends(verify_token)):
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