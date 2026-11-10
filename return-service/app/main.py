import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

app = FastAPI(title="Return Service")

security = HTTPBearer()

engine = create_engine(
    "sqlite:///./returns.db",
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


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


class ReturnRequest(Base):
    __tablename__ = "return_requests"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(String, default="REQUESTED")


Base.metadata.create_all(bind=engine)


class ReturnData(BaseModel):
    order_id: int = Field(gt=0)
    reason: str = Field(min_length=3)


@app.get("/")
def home():
    return {"message": "Return Service is running"}


@app.post("/returns")
def create_return(
    data: ReturnData,
    user_id: int = Depends(verify_token)
):
    db = SessionLocal()

    try:
        request = ReturnRequest(
            order_id=data.order_id,
            user_id=user_id,
            reason=data.reason,
            status="REQUESTED"
        )

        db.add(request)
        db.commit()
        db.refresh(request)

        return {
            "message": "Return request created",
            "return_id": request.id,
            "user_id": request.user_id,
            "order_id": request.order_id,
            "status": request.status
        }

    finally:
        db.close()


@app.get("/returns")
def get_returns(
    user_id: int = Depends(verify_token)
):
    db = SessionLocal()

    try:
        requests = db.query(ReturnRequest).filter(
            ReturnRequest.user_id == user_id
        ).all()

        return [
            {
                "return_id": item.id,
                "order_id": item.order_id,
                "reason": item.reason,
                "status": item.status
            }
            for item in requests
        ]

    finally:
        db.close()


@app.patch("/returns/{return_id}/status")
def update_return_status(
    return_id: int,
    status: str,
    user_id: int = Depends(verify_token)
):
    allowed = ["REQUESTED", "APPROVED", "REJECTED", "REFUNDED"]

    if status not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Invalid return status"
        )

    db = SessionLocal()

    try:
        item = db.query(ReturnRequest).filter(
            ReturnRequest.id == return_id,
            ReturnRequest.user_id == user_id
        ).first()

        if not item:
            raise HTTPException(
                status_code=404,
                detail="Return request not found"
            )

        item.status = status
        db.commit()

        return {
            "message": "Return status updated",
            "return_id": item.id,
            "status": item.status
        }

    finally:
        db.close()