from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

app = FastAPI(title="Return Service")

engine = create_engine(
    "sqlite:///./returns.db",
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


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
    user_id: int = Field(gt=0)
    reason: str = Field(min_length=3)


@app.get("/")
def home():
    return {"message": "Return Service is running"}


@app.post("/returns")
def create_return(data: ReturnData):
    db = SessionLocal()
    try:
        request = ReturnRequest(
            order_id=data.order_id,
            user_id=data.user_id,
            reason=data.reason,
            status="REQUESTED"
        )
        db.add(request)
        db.commit()
        db.refresh(request)

        return {
            "message": "Return request created",
            "return_id": request.id,
            "order_id": request.order_id,
            "status": request.status
        }
    finally:
        db.close()


@app.get("/returns/{user_id}")
def get_returns(user_id: int):
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
def update_return_status(return_id: int, status: str):
    allowed = ["REQUESTED", "APPROVED", "REJECTED", "REFUNDED"]

    if status not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Invalid return status"
        )

    db = SessionLocal()
    try:
        item = db.query(ReturnRequest).filter(
            ReturnRequest.id == return_id
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