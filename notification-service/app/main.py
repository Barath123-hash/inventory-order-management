import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

app = FastAPI(title="Notification Service")

security = HTTPBearer()

engine = create_engine(
    "sqlite:///./notifications.db",
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


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String, default="UNREAD")


Base.metadata.create_all(bind=engine)


class NotificationData(BaseModel):
    message: str


@app.get("/")
def home():
    return {"message": "Notification Service is running"}


@app.post("/notifications")
def create_notification(
    data: NotificationData,
    user_id: int = Depends(verify_token)
):
    db = SessionLocal()

    try:
        notification = Notification(
            user_id=user_id,
            message=data.message,
            status="UNREAD"
        )

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return {
            "message": "Notification created",
            "notification_id": notification.id,
            "user_id": notification.user_id,
            "notification": notification.message,
            "status": notification.status
        }

    finally:
        db.close()


@app.get("/notifications")
def get_notifications(
    user_id: int = Depends(verify_token)
):
    db = SessionLocal()

    try:
        items = db.query(Notification).filter(
            Notification.user_id == user_id
        ).all()

        return [
            {
                "notification_id": item.id,
                "message": item.message,
                "status": item.status
            }
            for item in items
        ]

    finally:
        db.close()